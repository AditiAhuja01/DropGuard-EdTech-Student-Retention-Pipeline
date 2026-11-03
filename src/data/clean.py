# src/data/clean.py
# Validates raw telemetry using Pydantic data models.
# Valid records are saved to data/clean/. Corrupted records are routed to data/quarantine/.

import os
import pandas as pd
from pydantic import BaseModel, EmailStr, field_validator, ValidationError
from typing import Optional
from datetime import date

# -------------------------------------------------------------
# 1. Pydantic Data Models (Data Quality Rules)
# -------------------------------------------------------------

class StudentModel(BaseModel):
    """Validates student profile data."""
    student_id: str
    student_name: str
    email: EmailStr  # Pydantic checks for a valid email format with '@' and domain
    signup_date: date

class EngagementLogModel(BaseModel):
    """Validates event log data from the course platform."""
    log_id: str
    student_id: str
    course_id: str
    event_type: str
    event_date: date
    watch_time_seconds: Optional[float] = None
    assignment_score: Optional[float] = None
    
    @field_validator('watch_time_seconds')
    @classmethod
    def check_watch_time(cls, v):
        if v is not None and v < 0:
            raise ValueError("Watch time cannot be negative")
        return v
        
    @field_validator('assignment_score')
    @classmethod
    def check_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Assignment score must be between 0 and 100")
        return v

# -------------------------------------------------------------
# 2. Validation & Quarantine Processing
# -------------------------------------------------------------

def clean_data():
    """
    Reads raw CSV files, applies Pydantic validation rules,
    and splits output into clean and quarantine folders.
    """
    print("[INFO] Starting data validation and quarantine pipeline...")
    
    os.makedirs("data/clean", exist_ok=True)
    os.makedirs("data/quarantine", exist_ok=True)
    
    # --- Validate Students ---
    print("[INFO] Validating Students dataset...")
    raw_students = pd.read_csv("data/raw/students.csv").to_dict(orient="records")
    clean_students, quarantine_students = [], []
    
    for row in raw_students:
        try:
            valid_student = StudentModel(**row)
            clean_students.append(valid_student.model_dump())
        except ValidationError as e:
            # Capture human-readable error reason for the quarantine file
            row['quarantine_reason'] = "Invalid email format (missing '@' or domain)"
            row['error_reason'] = str(e).replace('\n', ' ')
            quarantine_students.append(row)
            
    pd.DataFrame(clean_students).to_csv("data/clean/students.csv", index=False)
    if quarantine_students:
        pd.DataFrame(quarantine_students).to_csv("data/quarantine/dirty_students.csv", index=False)
        
    print(f"[SUCCESS] Students - Valid: {len(clean_students)} | Quarantined: {len(quarantine_students)}")

    # --- Validate Engagement Logs ---
    print("[INFO] Validating Engagement Logs dataset...")
    raw_logs = pd.read_csv("data/raw/engagement_logs.csv")
    raw_logs = raw_logs.where(pd.notnull(raw_logs), None).to_dict(orient="records")
    clean_logs, quarantine_logs = [], []
    
    for row in raw_logs:
        try:
            valid_log = EngagementLogModel(**row)
            clean_logs.append(valid_log.model_dump())
        except ValidationError as e:
            # Categorize the quarantine reason
            reasons = []
            if row.get('watch_time_seconds') is not None and row['watch_time_seconds'] < 0:
                reasons.append("Negative video watch time")
            if row.get('assignment_score') is not None and (row['assignment_score'] < 0 or row['assignment_score'] > 100):
                reasons.append("Assignment score outside 0-100 range")
            
            row['quarantine_reason'] = "; ".join(reasons) if reasons else "Schema validation failure"
            row['error_reason'] = str(e).replace('\n', ' ')
            quarantine_logs.append(row)
            
    pd.DataFrame(clean_logs).to_csv("data/clean/engagement_logs.csv", index=False)
    if quarantine_logs:
        pd.DataFrame(quarantine_logs).to_csv("data/quarantine/dirty_logs.csv", index=False)
        
    print(f"[SUCCESS] Logs - Valid: {len(clean_logs)} | Quarantined: {len(quarantine_logs)}")
    
    # --- Pass Through Already Clean Reference Tables ---
    pd.read_csv("data/raw/instructors.csv").to_csv("data/clean/instructors.csv", index=False)
    pd.read_csv("data/raw/courses.csv").to_csv("data/clean/courses.csv", index=False)
    pd.read_csv("data/raw/enrollments.csv").to_csv("data/clean/enrollments.csv", index=False)
    
    print("[SUCCESS] Data validation and quarantine complete. Clean files are ready for DuckDB.")

if __name__ == '__main__':
    clean_data()
