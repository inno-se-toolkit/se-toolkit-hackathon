# 📊 Grade Calculator — Version 2

A simple web app that calculates final grades, determine letter grades, and tell you **what grade you need to hit your target**. Each course can define its own grading scale.

**Version 2** — Everything from V1, plus:
- 🎯 **"What do I need to pass?"** — Enter a target grade, see what you need on remaining work
- 🔤 **Letter grading system** — A / B / C / D / F per course
- 📝 **Course-specific grading scales** — Each course defines its own A/B/C/D thresholds
- 💾 **Save / Load / Delete courses** — SQLite persistence
- ✨ **Improved UI** — Tabs, course list, toast notifications

---

## 🚀 How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn main:app --reload
```

### 3. Open in browser

**http://localhost:8000**

---

## 📁 Project Structure

```
se-toolkit-hackathon/
├── main.py              # FastAPI backend (all endpoints + DB logic)
├── models.py            # Pydantic models (V1 + V2)
├── requirements.txt     # Python dependencies
├── grades.db            # SQLite database (auto-created)
├── test_v2.py           # Smoke tests
└── static/
    └── index.html       # Frontend (HTML + CSS + JS)
```

---

## 🔌 API Endpoints

### V1 (unchanged)

#### `POST /calculate`

Calculate the final weighted grade.

**Request:**
```json
{
    "entries": [
        {"name": "Homework", "grade": 80, "weight": 20},
        {"name": "Midterm", "grade": 70, "weight": 30},
        {"name": "Final Exam", "grade": 90, "weight": 50}
    ]
}
```

**Response:**
```json
{
    "final_grade": 82.0,
    "total_weight": 100.0,
    "status": "Pass",
    "message": "Congratulations! You passed."
}
```

---

### V2 — Enhanced Calculation

#### `POST /calculate/v2`

Calculate with letter grade, custom grading scale, and "what do I need?" analysis.

**Request:**
```json
{
    "entries": [
        {"name": "Midterm", "grade": 75, "weight": 40},
        {"name": "Final", "grade": 85, "weight": 60}
    ],
    "target_grade": 80.0,
    "thresholds": {
        "a": 90,
        "b": 80,
        "c": 70,
        "d": 60
    }
}
```

**Response:**
```json
{
    "final_grade": 81.0,
    "letter_grade": "B",
    "total_weight": 100.0,
    "status": "Pass",
    "message": "Congratulations! You passed.",
    "required_for_target": 86.67,
    "thresholds_used": {
        "a": 90.0,
        "b": 80.0,
        "c": 70.0,
        "d": 60.0
    }
}
```

| Field | Description |
|-------|-------------|
| `final_grade` | Calculated weighted grade |
| `letter_grade` | A, B, C, D, or F based on thresholds |
| `required_for_target` | Grade needed on remaining weight to hit target (null if no target set) |
| `thresholds_used` | The grading scale that was applied |

---

### V2 — Course CRUD

#### `POST /courses` — Save a course

**Request:**
```json
{
    "name": "CS101 - Intro to Programming",
    "entries": [
        {"name": "Homework", "grade": 85, "weight": 20},
        {"name": "Midterm", "grade": 78, "weight": 30},
        {"name": "Final", "grade": 92, "weight": 50}
    ],
    "thresholds": {
        "a": 90,
        "b": 80,
        "c": 70,
        "d": 60
    }
}
```

**Response (201):**
```json
{
    "id": 1,
    "name": "CS101 - Intro to Programming",
    "entries": [ ... ],
    "thresholds": { "a": 90.0, "b": 80.0, "c": 70.0, "d": 60.0 },
    "final_grade": 86.4,
    "letter_grade": "B"
}
```

#### `GET /courses` — List all courses

**Response:**
```json
{
    "courses": [
        {
            "id": 1,
            "name": "CS101 - Intro to Programming",
            "entries": [ ... ],
            "thresholds": { ... },
            "final_grade": 86.4,
            "letter_grade": "B"
        }
    ]
}
```

#### `GET /courses/{id}` — Get one course

**Response:** Same structure as a single course in the list above.

**404 if not found:**
```json
{
    "detail": "Course not found."
}
```

#### `DELETE /courses/{id}` — Delete a course

**Response:**
```json
{
    "message": "Course deleted successfully."
}
```

---

## 🧮 Calculations

### Weighted Final Grade
```
final_grade = Σ(grade × weight) / Σ(weight)
```

### Letter Grade
Based on per-course thresholds:
- **A** if grade ≥ threshold_a
- **B** if grade ≥ threshold_b
- **C** if grade ≥ threshold_c
- **D** if grade ≥ threshold_d
- **F** if grade < threshold_d

### Required Grade for Target
```
required = (target × 100 - current_weighted_sum) / remaining_weight
```
- If result > 100 → target is impossible with remaining weight
- If result < 0 → target is already exceeded

---

## 🖥 Frontend Features

| Feature | Description |
|---------|-------------|
| **Calculator tab** | Enter grades, weights, set target, set grading scale, calculate |
| **Saved Courses tab** | View, load, and delete saved courses |
| **Target grade input** | Optional — shows required grade on remaining components |
| **Grading scale inputs** | Custom A/B/C/D thresholds per course |
| **Toast notifications** | Success/error feedback for all actions |
| **Responsive design** | Works on mobile and desktop |

---

## 🛠 Tech Stack

- **Backend:** Python FastAPI
- **Database:** SQLite (auto-created as `grades.db`)
- **Frontend:** Vanilla HTML + CSS + JavaScript (no frameworks)
- **Validation:** Pydantic models

---

## 🧪 Running Tests

```bash
python test_v2.py
```

Tests cover:
1. Weighted grade calculation
2. Letter grade (default thresholds)
3. Letter grade (custom thresholds)
4. Required grade for target
5. Impossible target detection
6. Database course creation
7. Database course loading
8. Database course listing
9. Database course deletion
10. V1 backward compatibility
11. V2 model validation
12. Frontend HTML serving

---

## 📋 Version Comparison

| Feature | V1 | V2 |
|---------|----|----|
| Calculate final grade | ✅ | ✅ |
| Letter grade (A-F) | ❌ | ✅ |
| Custom grading scale per course | ❌ | ✅ |
| Target grade / "What do I need?" | ❌ | ✅ |
| Save courses to database | ❌ | ✅ |
| Load saved courses | ❌ | ✅ |
| Delete courses | ❌ | ✅ |
| Course management UI | ❌ | ✅ |
