import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def calculate_frustration_scores():
    print("====================================")
    print(" PHASE 5: ADVANCED SQL SCORING      ")
    print("====================================")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Clear any old scores (idempotency)
        cursor.execute("TRUNCATE TABLE INTERVENTION_LOG;")
        
        # 2. STEP 1: Aggregate early engagement metrics per student (Standard JOIN + GROUP BY)
        cursor.execute("DROP TABLE IF EXISTS EarlyMetrics;")
        cursor.execute("""
        CREATE TEMP TABLE EarlyMetrics AS
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

        # 3. STEP 2: Compute 50/30/20 Frustration Score & Insert At-Risk students (> 50 score)
        insert_sql = """
        INSERT INTO INTERVENTION_LOG (student_id, course_id, frustration_score, category, action_recommended)
        SELECT 
            student_id,
            course_id,
            ROUND(CAST(
                LEAST(100.0, GREATEST(0.0, (4.0 - early_logins) * 25.0)) * 0.50 +
                LEAST(100.0, GREATEST(0.0, (1800.0 - early_watch_time) / 18.0)) * 0.30 +
                COALESCE(LEAST(100.0, GREATEST(0.0, (75.0 - avg_score) * 2.5)), 100.0) * 0.20
            AS NUMERIC), 1) AS frustration_score,
            
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
        """
        
        print("Executing straightforward 2-Step SQL Scoring Pipeline...")
        cursor.execute(insert_sql)
        
        # Check how many students were flagged
        cursor.execute("SELECT COUNT(*) FROM INTERVENTION_LOG;")
        flagged_count = cursor.fetchone()[0]
        
        print(f"SUCCESS: Computed Frustration Scores via SQL without complex CTEs!")
        print(f"RESULTS: Flagged {flagged_count} at-risk students and inserted them into INTERVENTION_LOG.")
        
    except Exception as e:
        print(f"ERROR: Something went wrong executing SQL on Cloud Database: {e}")
        print("\n💡 NOTE: You can run the entire pipeline & dashboard locally in zero clicks using:")
        print("   streamlit run app.py")
        print("   (This runs the exact same 50/30/20 SQL scoring in-memory via DuckDB with clean data).")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    calculate_frustration_scores()
