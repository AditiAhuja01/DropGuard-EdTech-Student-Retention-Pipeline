import os
import duckdb
import pandas as pd

def build_local_database():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    data_dir = os.path.join(project_root, "data", "clean")
    
    con = duckdb.connect(database=":memory:")
    
    c_csv = os.path.join(data_dir, "courses.csv").replace("\\", "/")
    i_csv = os.path.join(data_dir, "instructors.csv").replace("\\", "/")
    s_csv = os.path.join(data_dir, "students.csv").replace("\\", "/")
    e_csv = os.path.join(data_dir, "enrollments.csv").replace("\\", "/")
    l_csv = os.path.join(data_dir, "engagement_logs.csv").replace("\\", "/")
    
    con.execute(f"CREATE TABLE Courses AS SELECT course_id, course_name, total_days, difficulty FROM read_csv_auto('{c_csv}')")
    con.execute(f"CREATE TABLE Instructors AS SELECT instructor_id, instructor_name, department FROM read_csv_auto('{i_csv}')")
    con.execute(f"CREATE TABLE Students AS SELECT student_id, student_name, email, CAST(signup_date AS DATE) AS signup_date FROM read_csv_auto('{s_csv}')")
    con.execute(f"CREATE TABLE Enrollments AS SELECT enrollment_id, student_id, course_id, CAST(enrollment_date AS DATE) AS enrollment_date FROM read_csv_auto('{e_csv}')")
    con.execute(f"CREATE TABLE Engagement_Logs AS SELECT log_id, student_id, course_id, event_type, CAST(event_date AS DATE) AS event_date, watch_time_seconds, assignment_score FROM read_csv_auto('{l_csv}')")
    
    # Step 1: Create EarlyMetrics table (Standard JOIN + GROUP BY)
    con.execute("""
    CREATE TABLE EarlyMetrics AS
    SELECT 
        e.student_id,
        e.course_id,
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
    GROUP BY e.student_id, e.course_id;
    """)
    
    # Step 2: Compute 50/30/20 Frustration Score & populate INTERVENTION_LOG
    con.execute("""
    CREATE TABLE INTERVENTION_LOG AS
    SELECT 
        student_id,
        course_id,
        ROUND(
            LEAST(100.0, GREATEST(0.0, (4.0 - early_logins) * 25.0)) * 0.50 +
            LEAST(100.0, GREATEST(0.0, (1800.0 - early_watch_time) / 18.0)) * 0.30 +
            COALESCE(LEAST(100.0, GREATEST(0.0, (75.0 - avg_score) * 2.5)), 100.0) * 0.20
        , 1) AS frustration_score,
        
        CASE 
            WHEN (
                LEAST(100.0, GREATEST(0.0, (4.0 - early_logins) * 25.0)) * 0.50 +
                LEAST(100.0, GREATEST(0.0, (1800.0 - early_watch_time) / 18.0)) * 0.30 +
                COALESCE(LEAST(100.0, GREATEST(0.0, (75.0 - avg_score) * 2.5)), 100.0) * 0.20
            ) >= 80 THEN 'High Risk - Drop Imminent'
            ELSE 'At Risk - Stalling'
        END AS category,
        
        CASE 
            WHEN (4.0 - early_logins) * 25.0 * 0.50 >= (1800.0 - early_watch_time) / 18.0 * 0.30 
            THEN 'Send automated SMS check-in (Absence pattern)'
            ELSE 'Send targeted encouraging email (Inaction pattern)'
        END AS action_recommended
    FROM EarlyMetrics
    WHERE (
        LEAST(100.0, GREATEST(0.0, (4.0 - early_logins) * 25.0)) * 0.50 +
        LEAST(100.0, GREATEST(0.0, (1800.0 - early_watch_time) / 18.0)) * 0.30 +
        COALESCE(LEAST(100.0, GREATEST(0.0, (75.0 - avg_score) * 2.5)), 100.0) * 0.20
    ) > 50.0;
    """)
    return con

if __name__ == "__main__":
    db = build_local_database()
    print("Database built successfully!")
    print("Students count:", db.execute("SELECT COUNT(*) FROM Students").fetchone()[0])
    print("Enrollments count:", db.execute("SELECT COUNT(*) FROM Enrollments").fetchone()[0])
    print("Intervention count:", db.execute("SELECT COUNT(*) FROM INTERVENTION_LOG").fetchone()[0])
