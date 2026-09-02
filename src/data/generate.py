import os
import random
import pandas as pd
from faker import Faker
from datetime import timedelta

def generate_dataset():
    # Fix the seed so the dataset is reproducible if you run it again
    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    # Create directory for raw CSV files
    os.makedirs("data/raw", exist_ok=True)
    
    print("Generating Instructors and Courses...")
    
    # 1. Instructors
    instructors = []
    for _ in range(15):
        instructors.append({
            "instructor_id": f"INST_{fake.unique.random_number(digits=4)}",
            "instructor_name": fake.name(),
            "department": random.choice(["Data Engineering", "Web Dev", "Marketing", "Data Science"])
        })
    pd.DataFrame(instructors).to_csv("data/raw/instructors.csv", index=False)

    # 2. Courses
    courses = []
    for i in range(25):
        courses.append({
            "course_id": f"CRS_{100 + i}",
            "course_name": f"{random.choice(['Advanced', 'Intro to', 'Mastering'])} {random.choice(['Python', 'SQL', 'Tableau', 'PowerBI'])}",
            "total_days": random.choice([30, 45, 60, 90]), # Course length
            "difficulty": random.choice(["Beginner", "Intermediate", "Advanced"])
        })
    pd.DataFrame(courses).to_csv("data/raw/courses.csv", index=False)

    print("Generating 500 Students...")
    
    # 3. Students
    students = []
    for _ in range(500):
        email = fake.email()
        # 🟢 DIRTY DATA INJECTION #1: 5% of emails will be malformed (missing '@')
        if random.random() < 0.05:
            email = email.replace("@", "_at_") 
            
        students.append({
            "student_id": f"STU_{fake.unique.random_number(digits=5)}",
            "student_name": fake.name(),
            "email": email,
            "signup_date": fake.date_between(start_date='-1y', end_date='-6m')
        })
    pd.DataFrame(students).to_csv("data/raw/students.csv", index=False)

    print("Enrolling students & Generating ~35,000 Engagement Logs...")
    
    # 4 & 5. Enrollments and Logs linked together
    enrollments = []
    logs = []
    events = ["login", "video_watch", "quiz_attempt", "forum_post"]

    for stu in students:
        # Each student takes 1 to 3 courses
        num_courses = random.randint(1, 3)
        chosen_courses = random.sample(courses, num_courses)
        
        for crs in chosen_courses:
            enrollment_date = fake.date_between(start_date=stu["signup_date"], end_date='today')
            
            enrollments.append({
                "enrollment_id": f"ENR_{fake.unique.random_number(digits=6)}",
                "student_id": stu["student_id"],
                "course_id": crs["course_id"],
                "enrollment_date": enrollment_date
            })
            
            # --- CHURN PERSONA LOGIC ---
            # We explicitly define the personas you wanted in the CV
            persona = random.choices(["Overwhelmed", "Stalled", "Hunter", "Completer"], weights=[0.2, 0.3, 0.25, 0.25])[0]
            
            total_days = crs["total_days"]
            active_days = total_days
            
            # Decide how many days a student is active based on persona
            if persona == "Overwhelmed":
                active_days = int(total_days * random.uniform(0.05, 0.20)) # Quits in first 20%
            elif persona == "Stalled":
                active_days = int(total_days * random.uniform(0.3, 0.6))   # Fizzles out halfway

            # Generate daily logs up until their 'active_days' runs out
            for day_offset in range(active_days):
                current_date = enrollment_date + timedelta(days=day_offset)
                
                # Probability of being active on any given day drops over time
                activity_chance = 1.0 - (day_offset / total_days)
                
                if random.random() < activity_chance:
                    # Do 1 to 4 actions on this day
                    for _ in range(random.randint(1, 4)):
                        event = random.choice(events)
                        
                        watch_secs = None
                        assignment_score = None
                        
                        if event == "video_watch":
                            watch_secs = random.randint(30, 900)
                            # 🟢 DIRTY DATA INJECTION #2: 5% of watch times are negative!
                            if random.random() < 0.05:
                                watch_secs = -random.randint(10, 100)
                                
                        if event == "quiz_attempt":
                            # Hunters ace quizzes. Overwhelmed fail.
                            if persona == "Hunter":
                                assignment_score = round(random.uniform(85, 100), 2)
                            elif persona == "Overwhelmed":
                                assignment_score = round(random.uniform(20, 50), 2)
                            else:
                                assignment_score = round(random.uniform(60, 95), 2)
                                
                            # 🟢 DIRTY DATA INJECTION #3: Null/Impossible Scores
                            if random.random() < 0.05:
                                assignment_score = 999.0 # Impossible score
                        
                        logs.append({
                            "log_id": f"LOG_{fake.unique.random_number(digits=8)}",
                            "student_id": stu["student_id"],
                            "course_id": crs["course_id"],
                            "event_type": event,
                            "event_date": current_date,
                            "watch_time_seconds": watch_secs,
                            "assignment_score": assignment_score
                        })

    pd.DataFrame(enrollments).to_csv("data/raw/enrollments.csv", index=False)
    pd.DataFrame(logs).to_csv("data/raw/engagement_logs.csv", index=False)
    
    print(f"SUCCESS: Generated {len(logs)} hyper-realistic engagement logs across {len(enrollments)} enrollments.")

if __name__ == "__main__":
    generate_dataset()
