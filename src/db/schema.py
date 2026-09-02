import os
import psycopg2
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def create_schema():
    print("Connecting to Supabase...")
    try:
        # Establish connection
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Define the exact 6 tables from your master plan
        schema_sql = """
        -- 1. Courses Table
        CREATE TABLE IF NOT EXISTS Courses (
            course_id VARCHAR(50) PRIMARY KEY,
            course_name VARCHAR(255) NOT NULL,
            total_days INT NOT NULL,
            difficulty VARCHAR(50)
        );

        -- 2. Instructors Table
        CREATE TABLE IF NOT EXISTS Instructors (
            instructor_id VARCHAR(50) PRIMARY KEY,
            instructor_name VARCHAR(255) NOT NULL,
            department VARCHAR(100)
        );

        -- 3. Students Table
        CREATE TABLE IF NOT EXISTS Students (
            student_id VARCHAR(50) PRIMARY KEY,
            student_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            signup_date DATE
        );

        -- 4. Enrollments Table
        CREATE TABLE IF NOT EXISTS Enrollments (
            enrollment_id VARCHAR(50) PRIMARY KEY,
            student_id VARCHAR(50) REFERENCES Students(student_id),
            course_id VARCHAR(50) REFERENCES Courses(course_id),
            enrollment_date DATE
        );

        -- 5. Engagement_Logs Table (where our 35k simulated logs will go)
        CREATE TABLE IF NOT EXISTS Engagement_Logs (
            log_id VARCHAR(50) PRIMARY KEY,
            student_id VARCHAR(50) REFERENCES Students(student_id),
            course_id VARCHAR(50) REFERENCES Courses(course_id),
            event_type VARCHAR(100),
            event_date DATE,
            watch_time_seconds INT,
            assignment_score FLOAT
        );

        -- 6. INTERVENTION_LOG Table
        CREATE TABLE IF NOT EXISTS INTERVENTION_LOG (
            intervention_id SERIAL PRIMARY KEY,
            student_id VARCHAR(50) REFERENCES Students(student_id),
            course_id VARCHAR(50) REFERENCES Courses(course_id),
            frustration_score FLOAT,
            category VARCHAR(100),
            action_recommended TEXT,
            logged_date DATE DEFAULT CURRENT_DATE
        );
        """
        
        cursor.execute(schema_sql)
        print("SUCCESS: Connected to Supabase and created your 6 database tables!")
        
    except psycopg2.OperationalError as e:
        print("ERROR: Could not connect to Supabase. This could be due to your network (IPv4/IPv6). Error:")
        print(e)
    except Exception as e:
        print(f"ERROR: An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_schema()
