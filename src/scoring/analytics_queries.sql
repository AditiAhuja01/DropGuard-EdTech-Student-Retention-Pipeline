-- ==============================================================================
-- DROPGUARD: CORE ANALYTICS ENGINE QUERIES
-- ==============================================================================
-- This file contains all 21 SQL queries utilized to derive business insights.
-- They range from beginner metrics all the way to advanced Cohort Retention.
-- ==============================================================================

-- 🟢 EASY TIER: Basic Understanding
-- Q1. Count total students in the database.
SELECT COUNT(student_id) AS total_students FROM Students;

-- Q2. Find the total number of enrollments for each course.
SELECT course_id, COUNT(enrollment_id) AS total_enrolled
FROM Enrollments GROUP BY course_id ORDER BY total_enrolled DESC;

-- Q3. List all distinct event types captured in our pipeline.
SELECT DISTINCT event_type FROM Engagement_Logs;

-- Q4. Identify students who signed up in the last 6 months.
SELECT student_id, student_name, signup_date FROM Students
WHERE signup_date >= CURRENT_DATE - INTERVAL '6 months';

-- Q5. Find any "dirty data" (negative watch times) that slipped through.
SELECT log_id, student_id, watch_time_seconds FROM Engagement_Logs
WHERE watch_time_seconds < 0;


-- 🟡 INTERMEDIATE TIER: Joins and Grouping
-- Q6. Find the names of students enrolled in "Advanced SQL" (assuming CRS_101 is an advanced SQL course).
SELECT s.student_name, c.course_name
FROM Students s
JOIN Enrollments e ON s.student_id = e.student_id
JOIN Courses c ON e.course_id = c.course_id
WHERE c.course_name LIKE '%SQL%';

-- Q7. Calculate the average quiz score across all courses, but only show those averaging below 60.
SELECT c.course_name, ROUND(AVG(l.assignment_score)::numeric, 2) AS avg_quiz_score
FROM Courses c
JOIN Engagement_Logs l ON c.course_id = l.course_id
WHERE l.event_type = 'quiz_attempt'
GROUP BY c.course_name HAVING AVG(l.assignment_score) < 60;

-- Q8. Find "Ghost" Students (enrolled but zero engagement logs).
SELECT s.student_id, s.student_name
FROM Students s
JOIN Enrollments e ON s.student_id = e.student_id
LEFT JOIN Engagement_Logs l ON s.student_id = l.student_id
WHERE l.log_id IS NULL;

-- Q9. Count the total watch time per student across all their courses.
SELECT student_id, SUM(watch_time_seconds) AS total_watch_time
FROM Engagement_Logs WHERE event_type = 'video_watch' GROUP BY student_id;

-- Q10. Find the average course length (total_days) by difficulty.
SELECT difficulty, ROUND(AVG(total_days),1) AS avg_length FROM Courses GROUP BY difficulty;

-- Q11. Count total logins per day to see peak platform usage.
SELECT event_date, COUNT(*) AS logins
FROM Engagement_Logs WHERE event_type = 'login' GROUP BY event_date ORDER BY event_date DESC;


-- 🔵 ADVANCED TIER: Date Math, CTEs, Window Functions
-- Q12. Find the exact "First 20% Milestone" date for every enrollment.
SELECT e.student_id, c.course_name,
    e.enrollment_date, e.enrollment_date + CAST(c.total_days * 0.2 AS INT) AS warning_date
FROM Enrollments e JOIN Courses c ON e.course_id = c.course_id;

-- Q13. Find the Top 3 most engaged students (by watch time) PER course using Window Functions.
WITH StudentWatchTimes AS (
    SELECT course_id, student_id, SUM(watch_time_seconds) AS total_watch_time
    FROM Engagement_Logs WHERE event_type = 'video_watch' GROUP BY course_id, student_id
),
RankedStudents AS (
    SELECT course_id, student_id, total_watch_time,
    ROW_NUMBER() OVER (PARTITION BY course_id ORDER BY total_watch_time DESC) as rank
    FROM StudentWatchTimes
)
SELECT * FROM RankedStudents WHERE rank <= 3;

-- Q14. Calculate a 7-day rolling average of logins.
WITH DailyLogins AS (
    SELECT event_date, COUNT(*) as daily_count FROM Engagement_Logs WHERE event_type = 'login' GROUP BY event_date
)
SELECT event_date, daily_count,
    ROUND(AVG(daily_count) OVER (ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS rolling_7d_avg
FROM DailyLogins;

-- Q15. Identify students who scored perfectly (100) on their first ever quiz.
WITH FirstQuizzes AS (
    SELECT student_id, assignment_score,
    ROW_NUMBER() OVER(PARTITION BY student_id ORDER BY event_date ASC) as attempt_num
    FROM Engagement_Logs WHERE event_type = 'quiz_attempt'
)
SELECT student_id FROM FirstQuizzes WHERE attempt_num = 1 AND assignment_score = 100;

-- Q16. Day-over-Day percentage change in platform logins.
WITH LoginCounts AS (
    SELECT event_date, COUNT(*) as logins FROM Engagement_Logs WHERE event_type='login' GROUP BY event_date
),
PrevGains AS (
    SELECT event_date, logins, LAG(logins) OVER(ORDER BY event_date) as prev_day_logins FROM LoginCounts
)
SELECT event_date, logins, prev_day_logins,
    ROUND(((logins - prev_day_logins)::numeric / NULLIF(prev_day_logins, 0)) * 100, 2) AS dod_percentage
FROM PrevGains;


-- 🟣 EXPERT TIER: Cohort Analysis and scoring
-- Q17. Monthly Cohort Retention (Students still active 30 days after signup)
WITH Cohorts AS (
    SELECT student_id, DATE_TRUNC('month', signup_date) AS cohort_month FROM Students
),
ActiveStatus AS (
    SELECT DISTINCT l.student_id
    FROM Engagement_Logs l
    JOIN Students s ON l.student_id = s.student_id
    WHERE l.event_date >= s.signup_date + INTERVAL '30 days'
)
SELECT c.cohort_month, COUNT(c.student_id) AS total_joined, COUNT(a.student_id) AS active_after_30_days,
ROUND((COUNT(a.student_id)::numeric / COUNT(c.student_id)) * 100, 2) AS retention_rate
FROM Cohorts c LEFT JOIN ActiveStatus a ON c.student_id = a.student_id
GROUP BY c.cohort_month ORDER BY c.cohort_month;

-- Q18. Detect abrupt drop-offs: Students who logged in 3 days in a row, then vanished.
WITH DailyInteractions AS (
    SELECT student_id, event_date, LAG(event_date, 1) OVER (PARTITION BY student_id ORDER BY event_date) as prev_day
    FROM Engagement_Logs WHERE event_type = 'login'
)
SELECT DISTINCT student_id FROM DailyInteractions WHERE event_date - prev_day > 14; -- 14 day silence

-- Q19. Compare a student's watch time against the overall average of the course.
WITH CourseAverages AS (
    SELECT course_id, AVG(watch_time_seconds) as avg_course_watch_time
    FROM Engagement_Logs WHERE event_type = 'video_watch' GROUP BY course_id
)
SELECT l.student_id, l.course_id, SUM(l.watch_time_seconds) AS student_total, c.avg_course_watch_time
FROM Engagement_Logs l JOIN CourseAverages c ON l.course_id = c.course_id
WHERE l.event_type = 'video_watch' GROUP BY l.student_id, l.course_id, c.avg_course_watch_time
HAVING SUM(l.watch_time_seconds) < c.avg_course_watch_time * 0.5;

-- Q20. Find what percentage of students end up in the INTERVENTION_LOG per course.
SELECT e.course_id, COUNT(DISTINCT e.student_id) AS total_students, COUNT(DISTINCT i.student_id) AS flagged_students,
ROUND((COUNT(DISTINCT i.student_id)::numeric / NULLIF(COUNT(DISTINCT e.student_id), 0)) * 100, 2) AS risk_rate
FROM Enrollments e LEFT JOIN INTERVENTION_LOG i ON e.student_id = i.student_id AND e.course_id = i.course_id
GROUP BY e.course_id ORDER BY risk_rate DESC;

-- Q21. The COMPLETE 50/30/20 Frustration Engine Algorithm.
WITH NormalizedWindow AS (
    SELECT e.student_id, e.course_id, e.enrollment_date, c.total_days,
    e.enrollment_date + CAST(c.total_days * 0.2 AS INT) AS early_warning_date
    FROM Enrollments e JOIN Courses c ON e.course_id = c.course_id
),
StudentAggregates AS (
    SELECT nw.student_id, nw.course_id,
        COUNT(l.log_id) FILTER (WHERE l.event_type = 'login') as early_logins,
        COALESCE(SUM(l.watch_time_seconds) FILTER (WHERE l.event_type = 'video_watch'), 0) as early_watch_time,
        AVG(l.assignment_score) FILTER (WHERE l.event_type = 'quiz_attempt') as avg_early_score
    FROM NormalizedWindow nw
    LEFT JOIN Engagement_Logs l ON nw.student_id = l.student_id AND nw.course_id = l.course_id
        AND l.event_date >= nw.enrollment_date AND l.event_date <= nw.early_warning_date
    GROUP BY nw.student_id, nw.course_id
)
SELECT student_id, course_id,
    -- 50% Absence, 30% Inaction, 20% Struggle
    ROUND(CAST((
        LEAST(100.0, GREATEST(0.0, (4.0 - COALESCE(early_logins, 0)) * 25.0)) * 0.50 +
        LEAST(100.0, GREATEST(0.0, (1800.0 - early_watch_time) / 18.0)) * 0.30 +
        CASE WHEN avg_early_score IS NULL THEN 20.0 ELSE LEAST(100.0, GREATEST(0.0, (75.0 - avg_early_score) * 2.5)) * 0.20 END
    ) AS NUMERIC), 1) AS frustration_score
FROM StudentAggregates WHERE early_watch_time < 5000;
