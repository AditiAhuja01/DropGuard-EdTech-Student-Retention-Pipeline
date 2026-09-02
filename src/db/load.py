import os
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from dotenv import load_dotenv

# Load connection string from the .env file we configured
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def bulk_upload_to_supabase(cursor, table_name, dataframe, columns):
    """
    A professional Data Engineeing function using `execute_values`. 
    Doing 50,000 standard INSERTs takes 5+ minutes.
    Using `execute_values` batches them in chunks, taking 5 seconds.
    """
    if dataframe.empty:
        return
        
    import numpy as np
    # Standardize empty values for PostgreSQL properly
    dataframe = dataframe.replace({np.nan: None})
    
    # Convert Dataframe rows into raw Python tuples
    records = [tuple(row) for row in dataframe[columns].to_numpy()]
    cols_string = ','.join(columns)
    
    # Using 'ON CONFLICT DO NOTHING' ensures we don't crash if we run this script twice and try to upload same data
    query = f"INSERT INTO {table_name} ({cols_string}) VALUES %s ON CONFLICT DO NOTHING"
    
    print(f"Uploading {len(records)} rows into the {table_name} table...")
    execute_values(cursor, query, records, page_size=1000)
    print(f"  -> Uploaded successfully.")

def main():
    print("====================================")
    print(" PHASE 4: CLOUD DATABASE UPLOAD     ")
    print("====================================")
    try:
        # Connect to Supabase via Session Pooler
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        print("Connected to Supabase successfully!\n")
        
        # 1. Instructors
        df_instructors = pd.read_csv("data/clean/instructors.csv")
        bulk_upload_to_supabase(cursor, "Instructors", df_instructors, ["instructor_id", "instructor_name", "department"])
        
        # 2. Courses
        df_courses = pd.read_csv("data/clean/courses.csv")
        bulk_upload_to_supabase(cursor, "Courses", df_courses, ["course_id", "course_name", "total_days", "difficulty"])
        
        # 3. Students
        df_students = pd.read_csv("data/clean/students.csv")
        bulk_upload_to_supabase(cursor, "Students", df_students, ["student_id", "student_name", "email", "signup_date"])
        
        # In the real world, quarantining a student means their children records (enrollments/logs) become "Orphans". 
        # We must filter out orphans before Postgres rejects them due to Foreign Key constraints!
        valid_student_ids = set(df_students["student_id"])
        
        # 4. Enrollments (Filtered)
        df_enrollments = pd.read_csv("data/clean/enrollments.csv")
        df_enrollments = df_enrollments[df_enrollments["student_id"].isin(valid_student_ids)]
        bulk_upload_to_supabase(cursor, "Enrollments", df_enrollments, ["enrollment_id", "student_id", "course_id", "enrollment_date"])
        
        # 5. Engagement Logs (Filtered)
        df_logs = pd.read_csv("data/clean/engagement_logs.csv")
        df_logs = df_logs[df_logs["student_id"].isin(valid_student_ids)]
        bulk_upload_to_supabase(cursor, "Engagement_Logs", df_logs, ["log_id", "student_id", "course_id", "event_type", "event_date", "watch_time_seconds", "assignment_score"])
        
        print("\nSUCCESS: Phase 4 is complete! All verified data is now live in your Supabase project.")

    except Exception as e:
        print(f"ERROR: Something went wrong during upload:\n{e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
