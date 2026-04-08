"""
Pydantic models for Grade Calculator - Version 2
==================================================
Extends Version 1 with:
- Course CRUD models
- Grading threshold models
- Enhanced calculate request/response (target grade, letter grade, required grade)
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================================
# Version 1 models (kept for backward compatibility)
# ============================================================================

class GradeEntry(BaseModel):
    """A single assignment with its grade and weight."""
    name: str = Field(..., example="Midterm Exam")
    grade: float = Field(..., ge=0, le=100, example=85.0)
    weight: float = Field(..., gt=0, example=30.0)


class CalculateRequest(BaseModel):
    """Request body for the /calculate endpoint (V1)."""
    entries: List[GradeEntry]


class CalculateResponse(BaseModel):
    """Response from the /calculate endpoint (V1)."""
    final_grade: float
    total_weight: float
    status: str
    message: str


# ============================================================================
# Version 2 - Grading thresholds
# ============================================================================

class GradingThresholds(BaseModel):
    """Letter grade thresholds for a course."""
    a: float = Field(..., ge=0, le=100, example=90.0, description="Minimum grade for A")
    b: float = Field(..., ge=0, le=100, example=80.0, description="Minimum grade for B")
    c: float = Field(..., ge=0, le=100, example=70.0, description="Minimum grade for C")
    d: float = Field(..., ge=0, le=100, example=60.0, description="Minimum grade for D")
    # F is anything below d threshold


class GradingThresholdInput(BaseModel):
    """Grading thresholds with validation (A > B > C > D)."""
    a: float = Field(..., ge=0, le=100, example=90.0)
    b: float = Field(..., ge=0, le=100, example=80.0)
    c: float = Field(..., ge=0, le=100, example=70.0)
    d: float = Field(..., ge=0, le=100, example=60.0)


# ============================================================================
# Version 2 - Enhanced calculation
# ============================================================================

class CalculateV2Request(BaseModel):
    """Enhanced calculate request with optional target grade."""
    entries: List[GradeEntry]
    target_grade: Optional[float] = Field(None, ge=0, le=100, example=70.0,
                                           description="Optional target final grade")
    thresholds: Optional[GradingThresholdInput] = Field(None,
                                                         description="Optional custom grading scale")


class CalculateV2Response(BaseModel):
    """Enhanced calculate response with letter grade and required grade."""
    final_grade: float
    letter_grade: str
    total_weight: float
    status: str
    message: str
    required_for_target: Optional[float] = Field(None, description="Grade needed on remaining weight to hit target")
    thresholds_used: GradingThresholds


# ============================================================================
# Version 2 - Course CRUD
# ============================================================================

class CourseCreate(BaseModel):
    """Request to create/save a course."""
    name: str = Field(..., min_length=1, max_length=200, example="CS101")
    entries: List[GradeEntry]
    thresholds: GradingThresholdInput


class CourseUpdate(BaseModel):
    """Request to update a course (partial update)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    entries: Optional[List[GradeEntry]] = None
    thresholds: Optional[GradingThresholdInput] = None


class CourseResponse(BaseModel):
    """Response for a single course."""
    id: int
    name: str
    entries: List[GradeEntry]
    thresholds: GradingThresholds
    final_grade: float
    letter_grade: str


class CourseListResponse(BaseModel):
    """Response listing all saved courses."""
    courses: List[CourseResponse]


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
