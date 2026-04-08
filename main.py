"""
Grade Calculator - Version 2
=============================
Extends Version 1 with:
- "What do I need to pass?" calculation
- Letter grading system with per-course thresholds
- Course save / load / delete via SQLite
- Improved frontend

Endpoints:
- POST /calculate        (V1 – unchanged)
- POST /calculate/v2     (V2 – target grade, letter grade, required grade)
- POST /courses          (create a course)
- GET  /courses          (list all courses)
- GET  /courses/{id}     (get one course)
- DELETE /courses/{id}   (delete a course)
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models import (
    CalculateRequest,
    CalculateResponse,
    CalculateV2Request,
    CalculateV2Response,
    CourseCreate,
    CourseResponse,
    CourseListResponse,
    CourseUpdate,
    GradingThresholds,
    GradingThresholdInput,
    GradeEntry,
    MessageResponse,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Easy Grade Calculator", version="2.0.0")

DB_PATH = Path(__file__).parent / "grades.db"

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                entries_json TEXT NOT NULL,
                threshold_a REAL NOT NULL DEFAULT 90,
                threshold_b REAL NOT NULL DEFAULT 80,
                threshold_c REAL NOT NULL DEFAULT 70,
                threshold_d REAL NOT NULL DEFAULT 60
            )
        """)


init_db()

# ---------------------------------------------------------------------------
# Core calculation logic
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS = GradingThresholds(a=90, b=80, c=70, d=60)


def get_letter_grade(score: float, thresholds: GradingThresholds) -> str:
    """Return letter grade based on thresholds."""
    if score >= thresholds.a:
        return "A"
    elif score >= thresholds.b:
        return "B"
    elif score >= thresholds.c:
        return "C"
    elif score >= thresholds.d:
        return "D"
    else:
        return "F"


def calculate_weighted_grade(entries: list[dict]) -> tuple[float, float]:
    """Return (final_grade, total_weight)."""
    total_weight = sum(e["weight"] for e in entries)
    if total_weight == 0:
        raise HTTPException(status_code=400, detail="Total weight cannot be zero.")
    weighted_sum = sum(e["grade"] * e["weight"] for e in entries)
    return round(weighted_sum / total_weight, 2), round(total_weight, 2)


def calculate_required_grade(current_weighted_sum: float, total_weight: float,
                              target: float, remaining_weight: float) -> float:
    """Calculate the grade needed on remaining components to hit target."""
    if remaining_weight <= 0:
        raise HTTPException(status_code=400,
                            detail="No remaining weight to calculate required grade.")
    needed = (target * total_weight - current_weighted_sum) / remaining_weight
    return round(needed, 2)


# ---------------------------------------------------------------------------
# V1 Endpoint (unchanged)
# ---------------------------------------------------------------------------

@app.post("/calculate", response_model=CalculateResponse)
def calculate_v1(req: CalculateRequest):
    """Calculate the final weighted grade (Version 1)."""
    if not req.entries:
        raise HTTPException(status_code=400, detail="Please provide at least one grade entry.")

    entries = [e.model_dump() for e in req.entries]
    final_grade, total_weight = calculate_weighted_grade(entries)

    status = "Pass" if final_grade >= 50 else "Fail"
    message = "Congratulations! You passed." if status == "Pass" else "Unfortunately, you did not pass."

    return CalculateResponse(
        final_grade=final_grade,
        total_weight=total_weight,
        status=status,
        message=message,
    )


# ---------------------------------------------------------------------------
# V2 Endpoint – enhanced calculation
# ---------------------------------------------------------------------------

@app.post("/calculate/v2", response_model=CalculateV2Response)
def calculate_v2(req: CalculateV2Request):
    """
    Enhanced calculation with:
    - Letter grade
    - Custom grading thresholds
    - Required grade to hit a target
    """
    if not req.entries:
        raise HTTPException(status_code=400, detail="Please provide at least one grade entry.")

    entries = [e.model_dump() for e in req.entries]
    thresholds = req.thresholds if req.thresholds else DEFAULT_THRESHOLDS

    # Validate thresholds ordering
    if not (thresholds.a > thresholds.b > thresholds.c > thresholds.d):
        raise HTTPException(status_code=400,
                            detail="Thresholds must be in descending order: A > B > C > D")

    final_grade, total_weight = calculate_weighted_grade(entries)
    letter_grade = get_letter_grade(final_grade, thresholds)

    # Calculate required grade for target
    required_for_target = None
    if req.target_grade is not None:
        current_weighted_sum = sum(e["grade"] * e["weight"] for e in entries)
        remaining_weight = 100.0 - total_weight  # assume 100% total

        if remaining_weight > 0:
            required_for_target = calculate_required_grade(
                current_weighted_sum, 100.0, req.target_grade, remaining_weight
            )
            # Clamp to 0-100 range for display
            if required_for_target > 100:
                required_for_target = round(required_for_target, 2)
            elif required_for_target < 0:
                required_for_target = 0.0

    # Convert input thresholds to output model (GradingThresholdInput -> GradingThresholds)
    thresholds_out = GradingThresholds(
        a=thresholds.a, b=thresholds.b, c=thresholds.c, d=thresholds.d
    )

    # D and below = Fail; C and above = Pass
    status = "Pass" if final_grade >= thresholds.c else "Fail"
    message = "Congratulations! You passed." if status == "Pass" else "Unfortunately, you did not pass."

    return CalculateV2Response(
        final_grade=final_grade,
        letter_grade=letter_grade,
        total_weight=total_weight,
        status=status,
        message=message,
        required_for_target=required_for_target,
        thresholds_used=thresholds_out,
    )


# ---------------------------------------------------------------------------
# Course CRUD Endpoints
# ---------------------------------------------------------------------------

@app.post("/courses", response_model=CourseResponse, status_code=201)
def create_course(course: CourseCreate):
    """Save a new course to the database."""
    # Validate thresholds
    if not (course.thresholds.a > course.thresholds.b > course.thresholds.c > course.thresholds.d):
        raise HTTPException(status_code=400,
                            detail="Thresholds must be in descending order: A > B > C > D")

    entries_json = json.dumps([e.model_dump() for e in course.entries])

    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO courses (name, entries_json, threshold_a, threshold_b, threshold_c, threshold_d)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (course.name, entries_json,
             course.thresholds.a, course.thresholds.b,
             course.thresholds.c, course.thresholds.d)
        )
        course_id = cursor.lastrowid

    return _get_course_by_id(course_id)


@app.get("/courses", response_model=CourseListResponse)
def list_courses():
    """List all saved courses."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()

    courses = []
    for row in rows:
        courses.append(_row_to_course_response(row))

    return CourseListResponse(courses=courses)


@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int):
    """Get a single course by ID."""
    return _get_course_by_id(course_id)


@app.delete("/courses/{course_id}", response_model=MessageResponse)
def delete_course(course_id: int):
    """Delete a course by ID."""
    with get_db() as conn:
        result = conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Course not found.")

    return MessageResponse(message=f"Course deleted successfully.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_course_by_id(course_id: int) -> CourseResponse:
    """Fetch a course by ID and convert to response model."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Course not found.")

    return _row_to_course_response(row)


def _row_to_course_response(row: sqlite3.Row) -> CourseResponse:
    """Convert a database row to CourseResponse."""
    entries_data = json.loads(row["entries_json"])
    entries = [GradeEntry(**e) for e in entries_data]

    thresholds = GradingThresholds(
        a=row["threshold_a"],
        b=row["threshold_b"],
        c=row["threshold_c"],
        d=row["threshold_d"],
    )

    # Calculate final grade for display
    if entries:
        final_grade, _ = calculate_weighted_grade([e.model_dump() for e in entries])
    else:
        final_grade = 0.0

    letter_grade = get_letter_grade(final_grade, thresholds)

    return CourseResponse(
        id=row["id"],
        name=row["name"],
        entries=entries,
        thresholds=thresholds,
        final_grade=final_grade,
        letter_grade=letter_grade,
    )


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    """Serve the frontend HTML page."""
    return FileResponse("static/index.html")
