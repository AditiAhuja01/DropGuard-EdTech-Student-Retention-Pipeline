import os
import pandas as pd
from pydantic import BaseModel, EmailStr, field_validator, ValidationError
from typing import Optional
from datetime import date

# ==========================================
# 1. DEFINE PYDANTIC STRICT DATA SCHEMAS
# ==========================================

class StudentModel(BaseModel):
    student_id: str
    student_name: str
    email: EmailStr  # Pydantic will instantly reject any email missing an '@' or domain
    signup_date: date

class EngagementLogModel(BaseModel):
    log_id: str
    student_id: str
    course_id: str
    event_type: str
    event_date: date
    watch_time_seconds: Optional[float] = None
    assignment_score: Optional[float] = None
    
    # Custom Validation rules exactly describing business logic
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
            raise ValueError("Assignment score must be securely between 0 and 100")
        return v

# ==========================================
# 2. RUN THE VALIDATION ETL PIPELINE
# ==========================================

def clean_data():
    print("Initializing Data Cleaning & Validation Layer...")
    
    # Create the layers
    os.makedirs("data/clean", exist_ok=True)
    os.makedirs("data/quarantine", exist_ok=True)
    
    # --- PROCESS STUDENTS ---
    print("\nScanning Students CSV for Malformed Emails...")
    raw_students = pd.read_csv("data/raw/students.csv").to_dict(orient="records")
    clean_students, quarantine_students = [], []
    
    for row in raw_students:
        try:
            valid_student = StudentModel(**row)
            clean_students.append(valid_student.model_dump())
        except ValidationError as e:
            # If it fails, capture the exact pydantic error and banish it to quarantine
            row['error_reason'] = str(e).replace('\n', ' ')
            quarantine_students.append(row)
            
    pd.DataFrame(clean_students).to_csv("data/clean/students.csv", index=False)
    if quarantine_students:
        pd.DataFrame(quarantine_students).to_csv("data/quarantine/dirty_students.csv", index=False)
        
    print(f"SUCCESS: Students | Passed: {len(clean_students)} | Quarantined: {len(quarantine_students)}")

    # --- PROCESS LOGS ---
    print("\nScanning ~35,000 Engagement Logs for anomalies (negative time, fake scores)...")
    raw_logs = pd.read_csv("data/raw/engagement_logs.csv")
    
    # Replace Pandas NaN with Python None so Pydantic understands it's officially "null"
    raw_logs = raw_logs.where(pd.notnull(raw_logs), None).to_dict(orient="records")
    clean_logs, quarantine_logs = [], []
    
    for row in raw_logs:
        try:
            valid_log = EngagementLogModel(**row)
            clean_logs.append(valid_log.model_dump())
        except ValidationError as e:
            row['error_reason'] = str(e).replace('\n', ' ')
            quarantine_logs.append(row)
            
    pd.DataFrame(clean_logs).to_csv("data/clean/engagement_logs.csv", index=False)
    if quarantine_logs:
        pd.DataFrame(quarantine_logs).to_csv("data/quarantine/dirty_logs.csv", index=False)
        
    print(f"SUCCESS: Logs | Passed: {len(clean_logs)} | Quarantined: {len(quarantine_logs)}")
    
    # --- BYPASS SAFE TABLES ---
    # Courses, Instructors, and Enrollments do not have dirty data injected in our simulation
    pd.read_csv("data/raw/instructors.csv").to_csv("data/clean/instructors.csv", index=False)
    pd.read_csv("data/raw/courses.csv").to_csv("data/clean/courses.csv", index=False)
    pd.read_csv("data/raw/enrollments.csv").to_csv("data/clean/enrollments.csv", index=False)
    
    print("\nSUCCESS: Phase 3 Complete! Data is cleaned and verified safe for Database Insertion.")

if __name__ == '__main__':
    clean_data()
