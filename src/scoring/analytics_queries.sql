-- ==============================================================================
-- DROPGUARD: CORE ANALYTICS SQL QUERIES (DuckDB)
-- ==============================================================================
-- Clean, beginner-friendly SQL queries used across the DropGuard analytics pipeline.
-- Each query uses only standard clauses: SELECT, FROM, JOIN, WHERE, GROUP BY, ORDER BY, CASE WHEN.
-- NO CTEs (WITH), NO window functions, NO nested subqueries.
-- ==============================================================================


-- Query 1: Total Active Students
-- Business Question: How many verified, non-quarantined students are currently in the system?
SELECT COUNT(student_id) AS total_students
FROM Students;


-- Query 2: Total Course Enrollments
-- Business Question: Across all courses, how many total enrollment registrations exist?
SELECT COUNT(enrollment_id) AS total_enrollments
FROM Enrollments;


-- Query 3: Students Flagged At Risk (Score >= 50)
-- Business Question: How many students are showing early signs of frustration or disengagement?
SELECT COUNT(student_id) AS total_at_risk
FROM INTERVENTION_LOG;


-- Query 4: Critical High-Risk Students (Score >= 80)
-- Business Question: How many students are at immediate risk of dropping out?
SELECT COUNT(student_id) AS critical_high_risk
FROM INTERVENTION_LOG
WHERE frustration_score >= 80;


-- Query 5: Average Frustration Score
-- Business Question: What is the average frustration score among students who need intervention?
SELECT ROUND(AVG(frustration_score), 1) AS avg_frustration_score
FROM INTERVENTION_LOG;


-- Query 6: Risk Category Breakdown
-- Business Question: How are at-risk students distributed between Stalling (50-79) and High Risk (80-100)?
SELECT 
    category AS risk_category, 
    COUNT(student_id) AS student_count
FROM INTERVENTION_LOG
GROUP BY category
ORDER BY student_count DESC;


-- Query 7: Drop Risk by Course Difficulty Level
-- Business Question: Which difficulty levels (Beginner, Intermediate, Advanced) produce the most at-risk students?
SELECT 
    c.difficulty, 
    COUNT(i.student_id) AS at_risk_count
FROM Courses c
JOIN INTERVENTION_LOG i ON c.course_id = i.course_id
GROUP BY c.difficulty
ORDER BY at_risk_count DESC;


-- Query 8: Average Video Watch Time vs Quiz Score per Course
-- Business Question: Is there a correlation between time spent watching lectures and quiz performance?
SELECT 
    c.course_name, 
    ROUND(AVG(l.watch_time_seconds), 0) AS avg_watch_seconds, 
    ROUND(AVG(l.assignment_score), 1) AS avg_quiz_score
FROM Engagement_Logs l
JOIN Courses c ON l.course_id = c.course_id
WHERE l.event_type IN ('video_watch', 'quiz_attempt')
GROUP BY c.course_name
ORDER BY avg_quiz_score ASC;


-- Query 9: Recommended Operational Intervention Hit-List
-- Business Question: Which specific students require action, what is their score, and what action is recommended?
SELECT 
    i.student_id, 
    s.student_name, 
    c.course_name, 
    i.frustration_score, 
    i.category, 
    i.action_recommended
FROM INTERVENTION_LOG i
JOIN Students s ON i.student_id = s.student_id
JOIN Courses c ON i.course_id = c.course_id
WHERE i.frustration_score >= 50.0
ORDER BY i.frustration_score DESC;
