# src/scoring/calculate.py
# Calculates the 50/30/20 Frustration Score for students using DuckDB.

import os
import sys

# Add project root to Python path so we can import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.db.local_db import build_local_database

def calculate_frustration_scores():
    """
    Builds the in-memory DuckDB database and calculates
    frustration scores for all enrolled students.
    """
    print("=" * 50)
    print("DROPGUARD: CALCULATING FRUSTRATION SCORES (DuckDB)")
    print("=" * 50)

    # Build local database from verified clean CSV files
    con = build_local_database()

    # Query the results
    total_students = con.execute("SELECT COUNT(*) FROM Students").fetchone()[0]
    total_enrollments = con.execute("SELECT COUNT(*) FROM Enrollments").fetchone()[0]
    flagged_students = con.execute("SELECT COUNT(*) FROM INTERVENTION_LOG").fetchone()[0]
    high_risk = con.execute("SELECT COUNT(*) FROM INTERVENTION_LOG WHERE frustration_score >= 80").fetchone()[0]
    stalling = con.execute("SELECT COUNT(*) FROM INTERVENTION_LOG WHERE frustration_score < 80").fetchone()[0]

    print(f"Total Enrolled Students: {total_students}")
    print(f"Total Course Enrollments: {total_enrollments}")
    print(f"Students Flagged (Score >= 50): {flagged_students}")
    print(f"  - High Risk (Score >= 80): {high_risk}")
    print(f"  - At Risk / Stalling (Score 50-79): {stalling}")
    print("=" * 50)
    print("Scoring calculation completed successfully.")

    return con

if __name__ == "__main__":
    calculate_frustration_scores()
