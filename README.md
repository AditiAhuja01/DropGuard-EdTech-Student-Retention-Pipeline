# DropGuard: Proactive EdTech Churn Analytics & Data Pipeline

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_Warehouse-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![DuckDB](https://img.shields.io/badge/DuckDB-In--Memory_Engine-FFF000?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive_App-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Pydantic](https://img.shields.io/badge/Pydantic-Data_Validation-E92063?style=flat&logo=pydantic&logoColor=white)](https://pydantic.dev)

DropGuard is an end-to-end Data Engineering and Business Intelligence pipeline designed to detect and prevent student dropouts (Churn) in online education platforms. Instead of waiting until a student disappears, DropGuard identifies at-risk behavior within the first 20% of a course's timeline using a transparent, rule-based 50/30/20 Frustration Engine implemented via SQL aggregations.

---

## Executive Summary & Problem Statement

### The Core Problem
Traditional churn dashboards in EdTech and SaaS are reactive. They report who stopped paying or who quit last month. By the time a student has been inactive for two weeks, intervention is usually too late. Furthermore, black-box machine learning models output churn probabilities without explaining why the student is struggling or what specific action customer success teams should take.

### The DropGuard Solution
DropGuard shifts analytics from reactive reporting to proactive operational intervention:
1. **Behavioral Telemetry Simulation:** Synthesizes realistic platform events (logins, video watch times, quiz attempts) across distinct persona trajectories (Overwhelmed, Stalled, Completer).
2. **Data Integrity & Quarantine Layer:** Employs Pydantic schemas to validate incoming telemetry, automatically rerouting corrupted rows (negative watch times, invalid emails, out-of-range quiz scores) to a quarantine locker without crashing database ingest.
3. **50/30/20 Analytical SQL Engine:** Calculates a normalized Frustration Score (0 to 100) using a 2-step relational SQL pipeline.
4. **Actionable Operations Sandbox:** Feeds directly into a high-performance Streamlit Dashboard that categorizes risk personas and generates specific automated next steps (tutoring, SMS check-in, or engagement emails).

---

## Architecture & Data Flow

```mermaid
graph TD
    subgraph "Phase 1: Telemetry Generation"
        A[Faker Behavioral Engine] -->|500 Students & 35k+ Events| B(Raw CSV Layer)
    end

    subgraph "Phase 2: Validation & Quarantine (ETL)"
        B -->|Pydantic Schema Validation| C{Data Quality Check}
        C -->|Valid Records| D[data/clean/ CSVs]
        C -->|Corrupted Records| E[data/quarantine/ Locker]
    end

    subgraph "Phase 3 & 4: Storage & Analytical Brain"
        D -->|Dual Engine: PostgreSQL / DuckDB| F[(Analytical Database)]
        F -->|2-Step SQL Pipeline: Early Aggregates & Penalty Scoring| G[50/30/20 Frustration Engine]
        G -->|Flagged Risk Cohorts| H[INTERVENTION_LOG Table]
    end

    subgraph "Phase 5: Operational UI"
        F -->|Live SQL Query Fetch| I[Streamlit Dark-Glass UI]
        H -->|Interactive Hit-List| I
    end
```

---

## The 50/30/20 Frustration Algorithm

DropGuard normalizes each student's course milestone to evaluate only their engagement within the first 20% of the course duration:

$$\text{Frustration Score} = (0.50 \times \text{Absence Penalty}) + (0.30 \times \text{Inaction Penalty}) + (0.20 \times \text{Struggle Penalty})$$

| Component | Weight | Metric Evaluated | Penalty Logic |
| :--- | :---: | :--- | :--- |
| **Absence** | **50%** | Login frequency vs. expectation | Penalizes students logging in fewer than 3 times during the initial window. |
| **Inaction** | **30%** | Video watch time volume | Penalizes total video duration under 30 minutes (1,800s). |
| **Struggle** | **20%** | Quiz attempts & average scores | Penalizes quiz scores below 75% or unattempted quizzes. |

### Automated Operational Triggers
- **Score >= 80**: High Risk - Drop Imminent
- **Score 50-79**: At Risk - Stalling
- **Dominant Penalty = Absence**: Trigger automated SMS check-in.
- **Dominant Penalty = Struggle**: Schedule 1-on-1 Academic Tutoring.
- **Dominant Penalty = Inaction**: Send targeted encouraging content & study plan email.

---

## Repository Structure

```text
DropGuard/
├── app.py                      # Interactive Streamlit Web Application
├── requirements.txt            # Python Dependencies
├── .env.example                # Environment Variable Template
├── .gitignore                  # Git Ignore Rules
├── README.md                   # Complete Documentation & Architecture Guide
│
├── src/                        # Modular Source Code
│   ├── data/
│   │   ├── generate.py         # Behavioral telemetry simulation engine
│   │   └── clean.py            # Pydantic data validation & quarantine ETL
│   ├── db/
│   │   ├── schema.py           # PostgreSQL DDL table definitions
│   │   ├── load.py             # Cloud PostgreSQL bulk ETL loader
│   │   └── local_db.py         # Standalone DuckDB local execution engine
│   └── scoring/
│       ├── calculate.py        # 2-Step SQL Frustration Scoring pipeline
│       └── analytics_queries.sql # Suite of 21 business analytics SQL queries
│
└── data/                       # Telemetry Storage
    ├── raw/                    # 5 Generated raw telemetry CSVs
    ├── clean/                  # 5 Validated clean CSVs
    └── quarantine/             # Corrupted data quarantine files
```

---

## Quickstart & How to Run

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/AditiAhuja01/DropGuard-EdTech-Student-Retention-Pipeline.git
cd DropGuard-EdTech-Student-Retention-Pipeline
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard (Instant Local Mode)
DropGuard includes built-in dual-engine support. You can run the entire pipeline and dashboard locally in zero clicks:
```bash
streamlit run app.py
```
The application will automatically initialize the local high-speed DuckDB engine using the validated telemetry dataset.

### 3. (Optional) Run with Cloud Supabase PostgreSQL
To connect to your cloud PostgreSQL database:
1. Copy `.env.example` to `.env`:
   ```env
   DATABASE_URL="postgresql://postgres.[YOUR-PROJECT]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
   ```
2. Run the cloud pipeline:
   ```bash
   # 1. Validate & Quarantine Dirty Data
   python src/data/clean.py

   # 2. Create Schema & Bulk Load Cloud PostgreSQL
   python src/db/schema.py
   python src/db/load.py

   # 3. Execute Cloud SQL Scoring
   python src/scoring/calculate.py

   # 4. Launch Dashboard
   streamlit run app.py
   ```

---

## Dashboard Modules

1. **Executive Overview:**
   - Real-time KPIs (Active Students, Total Enrollments, Cohort Risk Rate).
   - Monthly Cohort Retention Curve computed via date-based group aggregations.
   - Risk Persona distribution donut chart.

2. **Course Analytics:**
   - Drop risk volume segmented by course difficulty level.
   - Correlation scatter plot between average video watch time and quiz performance.

3. **Intervention Sandbox:**
   - Interactive slider filtering students by Frustration Score threshold.
   - Automated action filtering (Tutoring vs SMS vs Email).
   - Operational student hit-list with visual progress indicators.

---

## Key Data Engineering Highlights for Interviews

- **Data Quality & Quarantine Patterns:** Demonstrates hands-on knowledge of dirty telemetry handling using Pydantic validation schemas and dead-letter quarantine files.
- **Relational SQL Pipeline:** Uses a clean, 2-step SQL pipeline (aggregating early telemetry with `JOIN` + `GROUP BY` and computing 50/30/20 penalty metrics with conditional logic).
- **Dual-Engine Architecture:** Seamless fallback between Cloud PostgreSQL (Supabase) and local DuckDB for resilient, high-speed execution.
- **Business Focus:** Connects data architecture directly to revenue retention and customer success workflows.
