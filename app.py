# app.py
# DropGuard: Student Retention & Early Churn Analytics Dashboard
# Clean, story-driven Streamlit interface powered by DuckDB in-memory analytics.

import os
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.db.local_db import build_local_database

# -------------------------------------------------------------
# 1. Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="DropGuard | Retention Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 2. Minimalist Light Corporate Theme Styling (Google Font: DM Sans)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    /* Global Typography and Background */
    html, body, [class*="css"] {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background-color: #F8FAFC;
    }

    /* Container padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 96% !important;
    }

    /* Metric Cards */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        border-top: 4px solid #4338CA;
    }
    .kpi-title {
        color: #64748B;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #0F172A;
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    .kpi-subtitle {
        color: #64748B;
        font-size: 0.8rem;
        margin-top: 6px;
    }

    /* Story Explainer Box */
    .story-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0D9488;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 1.5rem;
        color: #334155;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Chart Captions */
    .chart-caption {
        font-size: 0.82rem;
        color: #64748B;
        margin-top: -6px;
        margin-bottom: 16px;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. Database Initialization (DuckDB In-Memory Cached)
# -------------------------------------------------------------
@st.cache_resource
def get_database():
    """Initializes in-memory DuckDB database from verified clean CSVs."""
    return build_local_database()

db = get_database()

def run_query(sql_query):
    """Executes a SQL query on the DuckDB database and returns a DataFrame."""
    return db.execute(sql_query).df()

# -------------------------------------------------------------
# 4. Sidebar Navigation
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### DropGuard")
    st.caption("Student Retention & Early Churn Analytics")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        [
            "1. The Problem",
            "2. The Solution",
            "3. Risk Overview",
            "4. Action List"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(
        """
        **Pipeline Stack**  
        - Python & Pydantic ETL  
        - DuckDB In-Memory Engine  
        - 50/30/20 Relational SQL  
        - Streamlit Analytics UI  
        """
    )
    st.caption("Engine: Local In-Memory DuckDB")

# -------------------------------------------------------------
# PAGE 1: THE PROBLEM
# -------------------------------------------------------------
if page == "1. The Problem":
    st.title("The Problem: Late Churn Detection Fails")
    
    st.markdown("""
    <div class="story-box">
        In online education, <b>over 60% of student dropouts occur within the first 2 weeks</b> of course enrollment. 
        Traditional analytics dashboards are reactive: they report students who stopped logging in 30 days ago. 
        By then, reminder emails and calls are ignored. <b>Early intervention during the first 20% of the course</b> 
        is the only window where engagement can be salvaged.
    </div>
    """, unsafe_allow_html=True)

    # 4 KPI Cards
    total_students = run_query("SELECT COUNT(*) FROM Students;").iloc[0, 0]
    total_enrollments = run_query("SELECT COUNT(*) FROM Enrollments;").iloc[0, 0]
    at_risk_count = run_query("SELECT COUNT(*) FROM INTERVENTION_LOG;").iloc[0, 0]
    high_risk_count = run_query("SELECT COUNT(*) FROM INTERVENTION_LOG WHERE frustration_score >= 80;").iloc[0, 0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #4338CA;">
            <div class="kpi-title">Active Students</div>
            <div class="kpi-value">{total_students:,}</div>
            <div class="kpi-subtitle">Verified clean student profiles</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #0D9488;">
            <div class="kpi-title">Total Enrollments</div>
            <div class="kpi-value">{total_enrollments:,}</div>
            <div class="kpi-subtitle">Across 25 catalog courses</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #D97706;">
            <div class="kpi-title">Students At Risk</div>
            <div class="kpi-value">{at_risk_count}</div>
            <div class="kpi-subtitle">Score &ge; 50 in first 20% window</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #DC2626;">
            <div class="kpi-title">Critical High Risk</div>
            <div class="kpi-value">{high_risk_count}</div>
            <div class="kpi-subtitle">Score &ge; 80 (Drop Imminent)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Engagement Drop-off Chart
    st.subheader("When Do Students Stop Engaging?")
    dropoff_query = """
    SELECT 
        CASE 
            WHEN e.persona = 'Overwhelmed' THEN 'Early Drop-off (First 20% of Days)'
            WHEN e.persona = 'Stalled' THEN 'Midway Stall (30% to 60% of Days)'
            ELSE 'Course Completer / Active'
        END AS engagement_window,
        COUNT(e.enrollment_id) AS total_enrollments
    FROM Enrollments e
    GROUP BY engagement_window
    ORDER BY total_enrollments DESC;
    """
    df_dropoff = run_query(dropoff_query)
    
    fig_dropoff = px.bar(
        df_dropoff,
        x="engagement_window",
        y="total_enrollments",
        color="engagement_window",
        color_discrete_map={
            "Early Drop-off (First 20% of Days)": "#DC2626",
            "Midway Stall (30% to 60% of Days)": "#D97706",
            "Course Completer / Active": "#0D9488"
        },
        labels={"engagement_window": "Student Disengagement Stage", "total_enrollments": "Number of Enrollments"}
    )
    fig_dropoff.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        showlegend=False,
        height=380,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_dropoff, use_container_width=True)
    st.markdown(
        "<p class='chart-caption'>Finding: Over 190 enrollments drop out during the first 20% of course duration. DropGuard targets this window.</p>",
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# PAGE 2: THE SOLUTION
# -------------------------------------------------------------
elif page == "2. The Solution":
    st.title("The Solution: 50/30/20 Frustration Algorithm")
    
    st.markdown("""
    <div class="story-box">
        Instead of using an unexplainable black-box machine learning model, DropGuard calculates an explainable 
        <b>Frustration Score (0 to 100)</b> using standard SQL. Every point penalty connects directly to a specific 
        business root cause and operational next step.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Formula Breakdown")
    st.latex(r"\text{Frustration Score} = (0.50 \times \text{Absence Penalty}) + (0.30 \times \text{Inaction Penalty}) + (0.20 \times \text{Struggle Penalty})")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3 Rule Cards
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.markdown("""
        <div class="kpi-card" style="border-top-color: #4338CA;">
            <div class="kpi-title">50% Absence Penalty</div>
            <div class="kpi-value" style="font-size: 1.4rem; color: #4338CA;">Logins &lt; 4</div>
            <div class="kpi-subtitle">Evaluates platform attendance in early window.<br><b>Action:</b> Automated SMS check-in</div>
        </div>
        """, unsafe_allow_html=True)
    with rc2:
        st.markdown("""
        <div class="kpi-card" style="border-top-color: #D97706;">
            <div class="kpi-title">30% Inaction Penalty</div>
            <div class="kpi-value" style="font-size: 1.4rem; color: #D97706;">Watch Time &lt; 30 min</div>
            <div class="kpi-subtitle">Evaluates video lecture consumption.<br><b>Action:</b> Targeted study guide email</div>
        </div>
        """, unsafe_allow_html=True)
    with rc3:
        st.markdown("""
        <div class="kpi-card" style="border-top-color: #DC2626;">
            <div class="kpi-title">20% Struggle Penalty</div>
            <div class="kpi-value" style="font-size: 1.4rem; color: #DC2626;">Quiz Score &lt; 75%</div>
            <div class="kpi-subtitle">Evaluates assessment failure or skipping.<br><b>Action:</b> 1-on-1 Academic Tutoring</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    # Example Walkthrough
    st.subheader("Worked Example: How a Real Student is Scored")
    st.markdown("""
    Consider a student **Priya Patel** enrolled in **Advanced SQL (60-day course)**.  
    Her first 20% milestone window is **Day 1 to Day 12**:

    | Metric | Actual Observed Activity | Benchmark Threshold | Calculation | Penalty Score |
    | :--- | :---: | :---: | :--- | :---: |
    | **Logins** | 1 login | 4 logins expected | `(4 - 1) * 25.0` | **75.0 / 100** |
    | **Video Watch Time** | 540 seconds (9 mins) | 1,800 seconds (30 mins) | `(1800 - 540) / 18.0` | **70.0 / 100** |
    | **Average Quiz Score** | 42.0% | 75.0% passing benchmark | `(75.0 - 42.0) * 2.5` | **82.5 / 100** |

    **Final Composite Score Calculation:**
    $$\\text{Score} = (0.50 \\times 75.0) + (0.30 \\times 70.0) + (0.20 \\times 82.5) = 37.5 + 21.0 + 16.5 = \\mathbf{75.0}$$

    - **Risk Category:** **At Risk - Stalling** (Score between 50 and 79)
    - **Recommended Action:** **Send automated SMS check-in** (Absence penalty contributes the largest share: 37.5 points)
    """)

# -------------------------------------------------------------
# PAGE 3: RISK OVERVIEW
# -------------------------------------------------------------
elif page == "3. Risk Overview":
    st.title("Cohort Risk Overview")
    st.markdown("Distribution of student risk cohorts, retention curves, and course difficulty breakdown.")
    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Student Risk Cohorts")
        risk_pie_query = """
        SELECT 
            CASE 
                WHEN i.frustration_score >= 80 THEN 'High Risk (Score >= 80)'
                WHEN i.frustration_score >= 50 THEN 'At Risk (Score 50-79)'
                ELSE 'Low Risk / On Track'
            END AS risk_tier,
            COUNT(e.enrollment_id) AS student_count
        FROM Enrollments e
        LEFT JOIN INTERVENTION_LOG i 
            ON e.student_id = i.student_id 
            AND e.course_id = i.course_id
        GROUP BY risk_tier;
        """
        df_risk_pie = run_query(risk_pie_query)
        
        fig_donut = px.pie(
            df_risk_pie,
            names="risk_tier",
            values="student_count",
            hole=0.6,
            color="risk_tier",
            color_discrete_map={
                "Low Risk / On Track": "#0D9488",
                "At Risk (Score 50-79)": "#D97706",
                "High Risk (Score >= 80)": "#DC2626"
            }
        )
        fig_donut.update_layout(
            template="plotly_white",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            height=360,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown(
            "<p class='chart-caption'>Donut chart: Isolates the ~7% of enrollments in urgent need of intervention.</p>",
            unsafe_allow_html=True
        )

    with col_chart2:
        st.subheader("Drop Risk by Course Difficulty")
        difficulty_query = """
        SELECT 
            c.difficulty, 
            COUNT(i.student_id) AS at_risk_count
        FROM Courses c
        JOIN INTERVENTION_LOG i ON c.course_id = i.course_id
        GROUP BY c.difficulty
        ORDER BY at_risk_count DESC;
        """
        df_diff = run_query(difficulty_query)
        
        fig_bar_diff = px.bar(
            df_diff,
            x="difficulty",
            y="at_risk_count",
            color="difficulty",
            color_discrete_map={
                "Beginner": "#0D9488",
                "Intermediate": "#D97706",
                "Advanced": "#DC2626"
            },
            labels={"difficulty": "Course Level", "at_risk_count": "At-Risk Students"}
        )
        fig_bar_diff.update_layout(
            template="plotly_white",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            showlegend=False,
            height=360,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_bar_diff, use_container_width=True)
        st.markdown(
            "<p class='chart-caption'>Finding: Advanced and Intermediate courses produce higher drop rates due to difficulty spikes.</p>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Monthly Cohort Retention Curve
    st.subheader("Monthly Cohort Retention Curve (30-Day Benchmark)")
    retention_query = """
    SELECT 
        strftime(s.signup_date, '%b %Y') AS signup_month,
        COUNT(DISTINCT s.student_id) AS total_enrolled,
        COUNT(DISTINCT CASE WHEN l.event_date >= s.signup_date + 30 THEN s.student_id END) AS active_after_30d,
        ROUND(COUNT(DISTINCT CASE WHEN l.event_date >= s.signup_date + 30 THEN s.student_id END) * 100.0 / COUNT(DISTINCT s.student_id), 1) AS retention_pct
    FROM Students s
    LEFT JOIN Engagement_Logs l ON s.student_id = l.student_id
    GROUP BY strftime(s.signup_date, '%b %Y'), strftime(s.signup_date, '%Y-%m')
    ORDER BY strftime(s.signup_date, '%Y-%m');
    """
    df_retention = run_query(retention_query)
    
    fig_retention = px.line(
        df_retention,
        x="signup_month",
        y="retention_pct",
        markers=True,
        line_shape="spline",
        color_discrete_sequence=["#4338CA"],
        labels={"signup_month": "Student Signup Cohort", "retention_pct": "30-Day Retention %"}
    )
    fig_retention.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=340,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(range=[40, 100])
    )
    st.plotly_chart(fig_retention, use_container_width=True)
    st.markdown(
        "<p class='chart-caption'>Trend: Student cohort retention stabilizes around 65%-75% without proactive early intervention.</p>",
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# PAGE 4: ACTION LIST
# -------------------------------------------------------------
else:
    st.title("Recommended Operational Actions")
    st.markdown("""
    <div class="story-box">
        This hit-list provides customer success and academic advisor teams with 
        <b>concrete, prioritized next steps</b>. Every recommendation is based on which penalty 
        contributed the most points to the student's frustration score.
    </div>
    """, unsafe_allow_html=True)

    # Filter Controls
    f_col1, f_col2 = st.columns([1, 1])
    with f_col1:
        score_threshold = st.slider("Filter by Minimum Frustration Score", min_value=50, max_value=95, value=50, step=5)
    with f_col2:
        action_filter = st.selectbox(
            "Filter by Recommended Action",
            [
                "All Recommended Actions",
                "Send automated SMS check-in (Absence pattern)",
                "Send targeted encouraging email (Inaction pattern)",
                "Schedule 1-on-1 Academic Tutoring (Struggle pattern)"
            ]
        )

    # Build Filter Query
    list_query = f"""
    SELECT 
        i.student_id AS "Student ID",
        s.student_name AS "Student Name",
        c.course_name AS "Course Name",
        c.difficulty AS "Difficulty",
        i.frustration_score AS "Frustration Score",
        i.category AS "Risk Level",
        i.action_recommended AS "Recommended Action"
    FROM INTERVENTION_LOG i
    JOIN Students s ON i.student_id = s.student_id
    JOIN Courses c ON i.course_id = c.course_id
    WHERE i.frustration_score >= {score_threshold}
    """
    if action_filter != "All Recommended Actions":
        list_query += f" AND i.action_recommended = '{action_filter}'"
        
    list_query += " ORDER BY i.frustration_score DESC;"
    
    df_actions = run_query(list_query)
    
    st.caption(f"Showing **{len(df_actions)}** students requiring intervention (Threshold: {score_threshold}+)")

    st.dataframe(
        df_actions,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Frustration Score": st.column_config.ProgressColumn(
                "Frustration Score",
                help="Score from 0 (Safe) to 100 (Immediate Dropout Risk)",
                format="%.1f",
                min_value=0,
                max_value=100
            )
        }
    )
    
    st.markdown(
        "<p class='chart-caption'>Note: Recommendations are rule-based operational guidance for academic success teams.</p>",
        unsafe_allow_html=True
    )
