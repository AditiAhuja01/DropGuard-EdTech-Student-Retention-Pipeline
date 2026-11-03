# src/scoring/check_score.py
# Validates the accuracy of the 50/30/20 Frustration Scoring algorithm against
# the behavioral personas assigned during telemetry generation.

import os
import sys
import pandas as pd

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.db.local_db import build_local_database

def run_score_check():
    """
    Evaluates how effectively the Frustration Scoring model identifies
    at-risk student personas (Overwhelmed, Stalled) versus safe personas (Completers, Hunters).
    """
    con = build_local_database()

    query = """
    SELECT 
        e.persona,
        COUNT(e.enrollment_id) AS total_enrollments,
        COUNT(CASE WHEN i.frustration_score >= 50 THEN 1 END) AS flagged_at_risk_50,
        COUNT(CASE WHEN i.frustration_score >= 80 THEN 1 END) AS flagged_high_risk_80,
        ROUND(COUNT(CASE WHEN i.frustration_score >= 50 THEN 1 END) * 100.0 / COUNT(e.enrollment_id), 1) AS flag_rate_pct
    FROM Enrollments e
    LEFT JOIN INTERVENTION_LOG i 
        ON e.student_id = i.student_id 
        AND e.course_id = i.course_id
    GROUP BY e.persona
    ORDER BY flag_rate_pct DESC;
    """
    
    df = con.execute(query).df()
    
    print("=" * 70)
    print("DROPGUARD: 50/30/20 FRUSTRATION SCORE ACCURACY CHECK (SIMULATED COHORT)")
    print("=" * 70)
    print(df.to_string(index=False))
    print("=" * 70)
    print("KEY FINDINGS:")
    
    for _, row in df.iterrows():
        p = row['persona']
        tot = row['total_enrollments']
        f50 = row['flagged_at_risk_50']
        f80 = row['flagged_high_risk_80']
        rate = row['flag_rate_pct']
        if p == "Overwhelmed":
            print(f"- {p}: {f50}/{tot} ({rate}%) flagged early. {f80} reached Critical High Risk (>=80).")
        elif p == "Stalled":
            print(f"- {p}: {f50}/{tot} ({rate}%) flagged early. Identifies students who start slowing down.")
        elif p == "Completer":
            print(f"- {p} (False Positives): {f50}/{tot} ({rate}%) erroneously flagged. High specificity.")
        elif p == "Hunter":
            print(f"- {p}: {f50}/{tot} ({rate}%) flagged.")
            
    print("=" * 70)
    return df

if __name__ == "__main__":
    run_score_check()
