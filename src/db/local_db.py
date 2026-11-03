# src/db/local_db.py
# Loads clean CSV files into an in-memory DuckDB database and runs the 50/30/20 SQL scoring pipeline.

import os
import duckdb

def build_local_database():
    """
    Creates an in-memory DuckDB database, registers the 5 clean CSV files,
    and calculates student Frustration Scores using clean, beginner-friendly SQL.
    """
    # Use the current working directory as project root.
    # On Streamlit Cloud, the app always runs from the repo root.
    # os.getcwd() works correctly both locally and on the cloud server.
    project_root = os.getcwd()
    data_dir = os.path.join(project_root, "data", "clean")
    
    con = duckdb.connect(database=":memory:")
    
    c_csv = os.path.join(data_dir, "courses.csv").replace("\\", "/")
    i_csv = os.path.join(data_dir, "instructors.csv").replace("\\", "/")
    s_csv = os.path.join(data_dir, "students.csv").replace("\\", "/")
    e_csv = os.path.join(data_dir, "enrollments.csv").replace("\\", "/")
    l_csv = os.path.join(data_dir, "engagement_logs.csv").replace("\\", "/")
    
    # ---------------------------------------------------------
    # 1. Base Tables (Loaded from clean CSV files)
    # ---------------------------------------------------------
    con.execute(f"CREATE TABLE Courses AS SELECT course_id, course_name, total_days, difficulty FROM read_csv_auto('{c_csv}')")
    con.execute(f"CREATE TABLE Instructors AS SELECT instructor_id, instructor_name, department FROM read_csv_auto('{i_csv}')")
    con.execute(f"CREATE TABLE Students AS SELECT student_id, student_name, email, CAST(signup_date AS DATE) AS signup_date FROM read_csv_auto('{s_csv}')")
    con.execute(f"CREATE TABLE Enrollments AS SELECT enrollment_id, student_id, course_id, CAST(enrollment_date AS DATE) AS enrollment_date, persona FROM read_csv_auto('{e_csv}')")
    con.execute(f"CREATE TABLE Engagement_Logs AS SELECT log_id, student_id, course_id, event_type, CAST(event_date AS DATE) AS event_date, watch_time_seconds, assignment_score FROM read_csv_auto('{l_csv}')")
    
    # ---------------------------------------------------------
    # 2. Step 1: Early Metrics Aggregation
    # Measures activity only within the first 20% of each course
    # ---------------------------------------------------------
    con.execute("""
    CREATE TABLE EarlyMetrics AS
    SELECT 
        e.student_id,
        e.course_id,
        e.persona,
        COUNT(CASE WHEN l.event_type = 'login' THEN 1 END) AS early_logins,
        COALESCE(SUM(CASE WHEN l.event_type = 'video_watch' THEN l.watch_time_seconds END), 0) AS early_watch_time,
        AVG(CASE WHEN l.event_type = 'quiz_attempt' THEN l.assignment_score END) AS avg_score
    FROM Enrollments e
    JOIN Courses c ON e.course_id = c.course_id
    LEFT JOIN Engagement_Logs l 
        ON e.student_id = l.student_id 
        AND e.course_id = l.course_id
        AND l.event_date >= e.enrollment_date 
        AND l.event_date <= e.enrollment_date + CAST(c.total_days * 0.2 AS INT)
    GROUP BY e.student_id, e.course_id, e.persona;
    """)

    # ---------------------------------------------------------
    # 3. Step 2: Student Penalty Scoring (0 to 100 per component)
    # - Absence (50%): Penalized if early logins < 4
    # - Inaction (30%): Penalized if watch time < 1,800 seconds (30 mins)
    # - Struggle (20%): Penalized if quiz average < 75% or quizzes unattempted
    # ---------------------------------------------------------
    con.execute("""
    CREATE TABLE StudentPenalties AS
    SELECT 
        student_id,
        course_id,
        persona,
        LEAST(100.0, GREATEST(0.0, (4.0 - early_logins) * 25.0)) AS absence_penalty,
        LEAST(100.0, GREATEST(0.0, (1800.0 - early_watch_time) / 18.0)) AS inaction_penalty,
        COALESCE(LEAST(100.0, GREATEST(0.0, (75.0 - avg_score) * 2.5)), 100.0) AS struggle_penalty
    FROM EarlyMetrics;
    """)
    
    # ---------------------------------------------------------
    # 4. Step 3: Populate INTERVENTION_LOG (Students with Score >= 50)
    # Applies 50/30/20 weights to determine composite Frustration Score
    # Includes original activity metrics for complete explainability
    # ---------------------------------------------------------
    con.execute("""
    CREATE TABLE INTERVENTION_LOG AS
    SELECT 
        p.student_id,
        p.course_id,
        p.persona,
        m.early_logins,
        ROUND(m.early_watch_time / 60.0, 0) AS early_watch_mins,
        ROUND(COALESCE(m.avg_score, 0.0), 1) AS early_quiz_avg,
        ROUND((p.absence_penalty * 0.50) + (p.inaction_penalty * 0.30) + (p.struggle_penalty * 0.20), 1) AS frustration_score,
        
        CASE 
            WHEN ((p.absence_penalty * 0.50) + (p.inaction_penalty * 0.30) + (p.struggle_penalty * 0.20)) >= 80 
            THEN 'High Risk - Drop Imminent'
            ELSE 'At Risk - Stalling'
        END AS category,
        
        CASE 
            WHEN (p.struggle_penalty * 0.20) >= (p.absence_penalty * 0.50) AND (p.struggle_penalty * 0.20) >= (p.inaction_penalty * 0.30)
            THEN 'Schedule 1-on-1 Academic Tutoring (Struggle pattern)'
            WHEN (p.absence_penalty * 0.50) >= (p.inaction_penalty * 0.30)
            THEN 'Send automated SMS check-in (Absence pattern)'
            ELSE 'Send targeted encouraging email (Inaction pattern)'
        END AS action_recommended
    FROM StudentPenalties p
    JOIN EarlyMetrics m 
        ON p.student_id = m.student_id 
        AND p.course_id = m.course_id
    WHERE ((p.absence_penalty * 0.50) + (p.inaction_penalty * 0.30) + (p.struggle_penalty * 0.20)) >= 50.0;
    """)
    
    return con

if __name__ == "__main__":
    db = build_local_database()
    print("[SUCCESS] Local DuckDB database initialized successfully.")
    print("Students count:", db.execute("SELECT COUNT(*) FROM Students").fetchone()[0])
    print("Enrollments count:", db.execute("SELECT COUNT(*) FROM Enrollments").fetchone()[0])
    print("Intervention count (Score >= 50):", db.execute("SELECT COUNT(*) FROM INTERVENTION_LOG").fetchone()[0])
    print("High Risk count (Score >= 80):", db.execute("SELECT COUNT(*) FROM INTERVENTION_LOG WHERE frustration_score >= 80").fetchone()[0])
