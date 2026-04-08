"""
Smoke test for V2 - direct function calls, no TestClient needed.
Tests the core logic and API contract without requiring httpx.
"""
import json
import sqlite3
from pathlib import Path

# Import the app and helpers
from main import (
    get_letter_grade,
    DEFAULT_THRESHOLDS,
    calculate_weighted_grade,
    calculate_required_grade,
    get_connection,
    init_db,
    _row_to_course_response,
    app,
)
from models import (
    GradeEntry,
    GradingThresholds,
    GradingThresholdInput,
    CalculateV2Request,
    CalculateV2Response,
    CourseCreate,
)

print("=" * 60)
print("TEST 1: Weighted grade calculation")
entries = [
    {"name": "Midterm", "grade": 75, "weight": 40},
    {"name": "Final", "grade": 85, "weight": 60}
]
final, total = calculate_weighted_grade(entries)
assert final == 81.0, f"Expected 81.0, got {final}"
assert total == 100.0
print(f"  Weighted grade: {final}% (weight: {total}%)")
print("  PASS")

print("=" * 60)
print("TEST 2: Letter grade - default thresholds")
letter = get_letter_grade(92, DEFAULT_THRESHOLDS)
assert letter == "A"
letter = get_letter_grade(85, DEFAULT_THRESHOLDS)
assert letter == "B"
letter = get_letter_grade(73, DEFAULT_THRESHOLDS)
assert letter == "C"
letter = get_letter_grade(62, DEFAULT_THRESHOLDS)
assert letter == "D"
letter = get_letter_grade(45, DEFAULT_THRESHOLDS)
assert letter == "F"
print(f"  92->{get_letter_grade(92, DEFAULT_THRESHOLDS)}, 85->{get_letter_grade(85, DEFAULT_THRESHOLDS)}, "
      f"73->{get_letter_grade(73, DEFAULT_THRESHOLDS)}, 62->{get_letter_grade(62, DEFAULT_THRESHOLDS)}, "
      f"45->{get_letter_grade(45, DEFAULT_THRESHOLDS)}")
print("  PASS")

print("=" * 60)
print("TEST 3: Custom letter grade thresholds")
custom = GradingThresholds(a=85, b=75, c=65, d=50)
assert get_letter_grade(83, custom) == "B"
assert get_letter_grade(76, custom) == "B"
assert get_letter_grade(50, custom) == "D"
print(f"  83->{get_letter_grade(83, custom)} (A=85,B=75,C=65,D=50)")
print("  PASS")

print("=" * 60)
print("TEST 4: Required grade for target")
# Current: 75*40 = 3000 weighted points, total weight = 100
# Target 80% of 100 = 8000, need 8000-3000 = 5000 from 60 weight = 83.33
# But we already have 85*60=5100 from Final, so total = 3000+5100=8100, grade=81
# For target 80: already at 81, so required = negative (already exceeded)
# Let's test with partial weight: only 40% graded, target 80
entries_partial = [{"name": "Midterm", "grade": 70, "weight": 40}]
current_sum = sum(e["grade"] * e["weight"] for e in entries_partial)
# Need 80*100 - 70*40 = 8000-2800 = 5200 from 60 remaining = 86.67
required = calculate_required_grade(current_sum, 100.0, 80.0, 60.0)
assert required == 86.67, f"Expected 86.67, got {required}"
print(f"  Current: 70% at 40 weight, Target: 80%, Need: {required}% on remaining 60%")
print("  PASS")

print("=" * 60)
print("TEST 5: Impossible target")
entries_bad = [{"name": "Test", "grade": 30, "weight": 90}]
current_sum = sum(e["grade"] * e["weight"] for e in entries_bad)
required = calculate_required_grade(current_sum, 100.0, 90.0, 10.0)
assert required > 100, f"Expected >100, got {required}"
print(f"  Required: {required}% (impossible)")
print("  PASS")

print("=" * 60)
print("TEST 6: Database - init and create course")
# Reset DB for clean test
db_path = Path(__file__).parent / "grades.db"
if db_path.exists():
    db_path.unlink()

init_db()

entries_data = [
    GradeEntry(name="Homework", grade=85, weight=20),
    GradeEntry(name="Midterm", grade=78, weight=30),
    GradeEntry(name="Final", grade=92, weight=50),
]
thresholds = GradingThresholdInput(a=90, b=80, c=70, d=60)

entries_json = json.dumps([e.model_dump() for e in entries_data])

with get_connection() as conn:
    cursor = conn.execute(
        """INSERT INTO courses (name, entries_json, threshold_a, threshold_b, threshold_c, threshold_d)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("CS101", entries_json, thresholds.a, thresholds.b, thresholds.c, thresholds.d)
    )
    course_id = cursor.lastrowid
    conn.commit()

assert course_id is not None and course_id > 0
print(f"  Course created with ID: {course_id}")
print("  PASS")

print("=" * 60)
print("TEST 7: Database - load course")
with get_connection() as conn:
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()

assert row is not None
assert row["name"] == "CS101"
resp = _row_to_course_response(row)
assert resp.id == course_id
assert resp.name == "CS101"
assert len(resp.entries) == 3
assert resp.letter_grade == "B"  # weighted avg ~84.6
print(f"  Loaded: '{resp.name}', Grade={resp.final_grade}%, Letter={resp.letter_grade}")
print("  PASS")

print("=" * 60)
print("TEST 8: Database - list courses")
with get_connection() as conn:
    rows = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
assert len(rows) == 1
print(f"  Found {len(rows)} course(s)")
print("  PASS")

print("=" * 60)
print("TEST 9: Database - delete course")
with get_connection() as conn:
    result = conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    assert result.rowcount == 1

with get_connection() as conn:
    rows = conn.execute("SELECT * FROM courses").fetchall()
assert len(rows) == 0
print("  Course deleted, list is empty")
print("  PASS")

print("=" * 60)
print("TEST 10: V1 endpoint still works (model check)")
from models import CalculateRequest, CalculateResponse
req = CalculateRequest(entries=[
    GradeEntry(name="HW", grade=80, weight=20),
    GradeEntry(name="Exam", grade=90, weight=80),
])
assert len(req.entries) == 2
print(f"  V1 models validate correctly")
print("  PASS")

print("=" * 60)
print("TEST 11: V2 request model validates")
req_v2 = CalculateV2Request(
    entries=[GradeEntry(name="Test", grade=80, weight=100)],
    target_grade=85.0,
    thresholds=GradingThresholdInput(a=90, b=80, c=70, d=60)
)
assert req_v2.target_grade == 85.0
assert req_v2.thresholds.a == 90
print(f"  V2 request model validates correctly")
print("  PASS")

print("=" * 60)
print("TEST 12: Frontend HTML exists")
html_path = Path(__file__).parent / "static" / "index.html"
assert html_path.exists()
html = html_path.read_text()
assert "Grade Calculator V2" in html
assert "threshold-a" in html
assert "target-grade" in html
assert "courses-list" in html
print("  Frontend has V2 features (thresholds, target, courses)")
print("  PASS")

print()
print("=" * 60)
print("ALL 12 TESTS PASSED!")
print("=" * 60)
