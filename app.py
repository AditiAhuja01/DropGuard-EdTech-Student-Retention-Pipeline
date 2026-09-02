import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# ==========================================
# PAGE SETTINGS & PREMIUM CSS
# ==========================================
st.set_page_config(
    page_title="DropGuard | Churn Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for a highly premium dark glassmorphism look
st.markdown("""
<style>
    .metric-card {
        background-color: #1A1C23;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #2D3748;
        border-left: 6px solid #6366F1;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-title { color: #A0AEC0; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #FFFFFF; font-size: 2.2rem; font-weight: bold; margin: 5px 0 0 0; }
    .metric-delta { color: #48BB78; font-size: 0.85rem; font-weight: 500;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE CONNECTION (CACHED)
# ==========================================
load_dotenv()

@st.cache_resource
def init_connection():
    # 1. Try Supabase / PostgreSQL if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            conn = psycopg2.connect(db_url, connect_timeout=4)
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return {"type": "postgres", "conn": conn}
        except Exception:
            pass
    
    # 2. Local standalone fallback using DuckDB + verified clean CSV dataset
    try:
        from src.db.local_db import build_local_database
        con = build_local_database()
        return {"type": "duckdb", "conn": con}
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        return None

db_handle = init_connection()

@st.cache_data(ttl=600)  # Cache queries for 10 minutes for snappy performance
def run_query(query):
    if not db_handle:
        return pd.DataFrame()
    
    if db_handle["type"] == "postgres":
        with db_handle["conn"].cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(cur.fetchall(), columns=columns)
    else:
        # DuckDB compatibility adaptation: only format month display
        adapted_query = query.replace("TO_CHAR(DATE_TRUNC('month', s.signup_date), 'Mon YYYY')", "strftime(DATE_TRUNC('month', s.signup_date), '%b %Y')")
        df = db_handle["conn"].execute(adapted_query).df()
        
    df.columns = df.columns.str.lower()
    return df

# ==========================================
# APP NAVIGATION 
# ==========================================
st.sidebar.image("https://img.icons8.com/nolan/256/shield.png", width=60)
st.sidebar.title("DropGuard")
if db_handle and db_handle["type"] == "postgres":
    st.sidebar.caption("Connected to Supabase Cloud")
else:
    st.sidebar.caption("Local Pipeline Engine (Clean Data)")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", 
    ["1. Executive Overview", "2. Course Analytics", "3. Intervention Sandbox"],
    label_visibility="collapsed"
)

# ==========================================
# PAGE 1: EXECUTIVE OVERVIEW
# ==========================================
if page == "1. Executive Overview":
    st.title("Executive Overview")
    st.markdown("Early-warning tracking system identifying students stalling out in the **First 20%** of their course timeline.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPIs
    kpi_data = run_query("""
        SELECT 
            (SELECT COUNT(*) FROM Students) as total_stu,
            (SELECT COUNT(*) FROM Enrollments) as total_enr,
            (SELECT COUNT(*) FROM INTERVENTION_LOG) as total_risk
    """)
    
    col1, col2, col3 = st.columns(3)
    c_risk = kpi_data['total_risk'].iloc[0]
    c_enr = kpi_data['total_enr'].iloc[0]
    risk_pct = (c_risk / c_enr) * 100 if c_enr > 0 else 0
    
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">Active Students</div>
        <div class="metric-value">{kpi_data['total_stu'].iloc[0]:,}</div><div class="metric-delta">+12% vs last month</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card" style="border-left-color: #48BB78;"><div class="metric-title">Total Enrollments</div>
        <div class="metric-value">{kpi_data['total_enr'].iloc[0]:,}</div><div class="metric-delta">Across 25 Active Courses</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card" style="border-left-color: #F56565;"><div class="metric-title">Critical At-Risk</div>
        <div class="metric-value">{c_risk}</div><div class="metric-delta" style="color:#F56565">{risk_pct:.1f}% cohort risk rate</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # CHARTS (Row 2)
    chart_col1, chart_col2 = st.columns([2, 1])
    
    with chart_col1:
        st.subheader("Monthly Cohort Retention Focus")
        retention_data = run_query("""
            SELECT 
                TO_CHAR(DATE_TRUNC('month', s.signup_date), 'Mon YYYY') AS month,
                COUNT(DISTINCT s.student_id) AS joined,
                COUNT(DISTINCT CASE WHEN l.event_date >= s.signup_date + INTERVAL '30 days' THEN s.student_id END) AS active,
                ROUND((COUNT(DISTINCT CASE WHEN l.event_date >= s.signup_date + INTERVAL '30 days' THEN s.student_id END) * 100.0 / COUNT(DISTINCT s.student_id)), 1) AS retention
            FROM Students s
            LEFT JOIN Engagement_Logs l ON s.student_id = l.student_id
            GROUP BY TO_CHAR(DATE_TRUNC('month', s.signup_date), 'Mon YYYY'), DATE_TRUNC('month', s.signup_date)
            ORDER BY DATE_TRUNC('month', s.signup_date)
        """)
        fig_retention = px.line(retention_data, x='month', y='retention', markers=True, 
                                line_shape='spline', color_discrete_sequence=['#6366F1'])
        fig_retention.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                    yaxis_title="Retention Rate %", xaxis_title="")
        st.plotly_chart(fig_retention, use_container_width=True)

    with chart_col2:
        st.subheader("Risk Persona Breakdown")
        intervention_data = run_query("SELECT category as Persona, COUNT(*) as amount FROM INTERVENTION_LOG GROUP BY category")
        fig_donut = px.pie(intervention_data, names='persona', values='amount', hole=0.7, 
                           color_discrete_sequence=['#F56565', '#ED8936', '#48BB78'])
        fig_donut.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
        st.plotly_chart(fig_donut, use_container_width=True)

# ==========================================
# PAGE 2: COURSE ANALYTICS
# ==========================================
elif page == "2. Course Analytics":
    st.title("Course Trajectory Analysis")
    st.markdown("Identifying engagement drop-offs based on course length and difficulty.")
    
    col1, col2 = st.columns(2)
    with col1:
        risk_by_course = run_query("""
            SELECT c.course_name, COUNT(i.student_id) as risk_count, c.difficulty
            FROM Courses c JOIN INTERVENTION_LOG i ON c.course_id = i.course_id
            GROUP BY c.course_name, c.difficulty ORDER BY risk_count DESC LIMIT 10
        """)
        fig_bar = px.bar(risk_by_course, x='risk_count', y='course_name', orientation='h', color='difficulty',
                         color_discrete_map={'Beginner':'#48BB78', 'Intermediate':'#ED8936', 'Advanced':'#F56565'},
                         title="Courses with Highest Drop Risk")
        fig_bar.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        watch_vs_score = run_query("""
            SELECT c.course_name, AVG(l.watch_time_seconds) as avg_watch, AVG(l.assignment_score) as avg_score
            FROM Engagement_Logs l JOIN Courses c ON l.course_id = c.course_id
            WHERE l.event_type IN ('video_watch', 'quiz_attempt') GROUP BY c.course_name
        """)
        fig_scatter = px.scatter(watch_vs_score, x='avg_watch', y='avg_score', size='avg_score', 
                                 hover_name='course_name', color='avg_watch', color_continuous_scale="Viridis",
                                 title="Score vs Watch Time Correlation")
        fig_scatter.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# PAGE 3: INTERVENTION SANDBOX
# ==========================================
else:
    st.title("Live Intervention Tracker")
    st.markdown("Targeted list of students requiring immediate action based on our **50/30/20 Frustration Engine** calculations.")
    
    # Filter Controls
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        min_score = st.slider("Minimum Frustration Score Filter", min_value=50, max_value=100, value=60)
    with filter_col2:
        action_filter = st.selectbox("Action Recommendation", ["All", "Schedule Academic Tutoring (Struggle pattern)", "Send automated SMS check-in (Absence pattern)", "Send targeted encouraging email (Inaction pattern)"])
    
    # Build Query
    query = f"""
        SELECT i.student_id, s.student_name, c.course_name, i.frustration_score, i.category, i.action_recommended
        FROM INTERVENTION_LOG i
        JOIN Students s ON i.student_id = s.student_id
        JOIN Courses c ON i.course_id = c.course_id
        WHERE i.frustration_score >= {min_score}
    """
    if action_filter != "All":
        query += f" AND i.action_recommended = '{action_filter}'"
        
    query += " ORDER BY i.frustration_score DESC"
    
    table_data = run_query(query)
    
    # Show Dataframe with custom column styling
    st.dataframe(
        table_data, 
        use_container_width=True,
        column_config={
            "frustration_score": st.column_config.ProgressColumn(
                "Frustration Score", min_value=0, max_value=100, format="%f"
            ),
            "category": "Risk Category",
            "action_recommended": "Automated Trigger",
            "student_name": "Student Name"
        },
        hide_index=True
    )
