
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Palo Alto Career Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# STYLE
# ============================================================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 16px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    files = [
        "Palo_Alto_Career_Progression_Final.csv",
        "Palo Alto Networks.csv",
        "Palo_Alto_Networks.csv"
    ]
    for file in files:
        try:
            return pd.read_csv(file), file
        except FileNotFoundError:
            pass
    return None, None

df, filename = load_data()

if df is None:
    st.error("❌ CSV file not found.")
    st.info("Put your CSV file in the same folder as app.py.")
    st.code(
        "Streamlit/\n"
        "├── app.py\n"
        "├── Palo Alto Networks.csv\n"
        "└── requirements.txt"
    )
    st.stop()

# ============================================================
# CLEAN COLUMN NAMES
# ============================================================
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
    .str.replace("-", "_", regex=False)
)

def find_column(names):
    normalized = {
        str(c).replace("_", "").replace(" ", "").lower(): c
        for c in df.columns
    }
    for name in names:
        key = name.replace("_", "").replace(" ", "").lower()
        if key in normalized:
            return normalized[key]
    return None

age_col = find_column(["age"])
gender_col = find_column(["gender", "sex"])
department_col = find_column(["department", "dept"])
job_level_col = find_column(["job_level", "joblevel", "job_level_name"])
job_role_col = find_column(["job_role", "jobrole", "role"])
experience_col = find_column([
    "years_at_company", "yearsatcompany",
    "years_experience", "experience",
    "total_working_years", "totalworkingyears"
])
promotion_col = find_column([
    "years_since_last_promotion",
    "yearssincelastpromotion",
    "years_since_promotion",
    "promotion",
    "promoted",
    "promotion_status"
])
attrition_col = find_column(["attrition", "left_company", "employee_status"])
satisfaction_col = find_column([
    "job_satisfaction", "jobsatisfaction",
    "satisfaction", "job_satisfaction_score"
])
overtime_col = find_column(["overtime", "over_time"])
worklife_col = find_column([
    "work_life_balance", "worklifebalance"
])
income_col = find_column([
    "monthly_income", "monthlyincome", "income", "salary"
])

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("📊 Palo Alto Analytics")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Executive Dashboard",
        "📊 Career Clusters",
        "📈 Promotion Gap",
        "🎯 Retention Opportunities",
        "👤 Employee Explorer"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Dataset: {filename}")
st.sidebar.caption(f"Rows: {len(df):,}")
st.sidebar.caption(f"Columns: {len(df.columns)}")

# ============================================================
# HEADER
# ============================================================
st.title("📊 Palo Alto Career Analytics")
st.caption("Employee career progression, promotion and retention analysis")
st.markdown("---")

# ============================================================
# EXECUTIVE DASHBOARD
# ============================================================
if page == "🏠 Executive Dashboard":

    st.header("🏠 Executive Dashboard")

    total = len(df)
    avg_age = df[age_col].mean() if age_col else None
    avg_exp = df[experience_col].mean() if experience_col else None

    if attrition_col:
        attrition_rate = (
            df[attrition_col].astype(str).str.lower()
            .isin(["yes", "true", "1", "left"])
            .mean() * 100
        )
    else:
        attrition_rate = None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Employees", f"{total:,}")
    c2.metric("🎂 Average Age", f"{avg_age:.1f}" if avg_age is not None else "N/A")
    c3.metric("💼 Avg. Experience", f"{avg_exp:.1f} yrs" if avg_exp is not None else "N/A")
    c4.metric("🚪 Attrition Rate", f"{attrition_rate:.1f}%" if attrition_rate is not None else "N/A")

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("🏢 Employees by Department")
        if department_col:
            x = df[department_col].value_counts().reset_index()
            x.columns = ["Department", "Employees"]
            fig = px.bar(x, x="Department", y="Employees",
                         title="Employee Distribution by Department")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Department column not available.")

    with right:
        st.subheader("👥 Employee Attrition")
        if attrition_col:
            x = df[attrition_col].astype(str).value_counts().reset_index()
            x.columns = ["Status", "Employees"]
            fig = px.pie(x, names="Status", values="Employees",
                         hole=0.45, title="Retention vs Attrition")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Attrition column not available.")

    if job_level_col:
        st.subheader("💼 Employees by Job Level")
        x = df[job_level_col].astype(str).value_counts().reset_index()
        x.columns = ["Job Level", "Employees"]
        fig = px.bar(x, x="Job Level", y="Employees",
                     title="Job Level Distribution")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# CAREER CLUSTERS
# ============================================================
elif page == "📊 Career Clusters":

    st.header("📊 Career Clusters")
    st.write("Employees are grouped into career stages using years of experience at the company.")

    if not experience_col:
        st.warning("No experience column was detected.")
        st.stop()

    work = df.copy()

    def career_cluster(v):
        if pd.isna(v):
            return "Unknown"
        if v < 3:
            return "Early Career"
        if v < 7:
            return "Mid Career"
        if v < 12:
            return "Experienced"
        return "Senior Career"

    work["Career Cluster"] = work[experience_col].apply(career_cluster)

    counts = work["Career Cluster"].value_counts().reset_index()
    counts.columns = ["Career Cluster", "Employees"]

    left, right = st.columns(2)

    with left:
        fig = px.bar(
            counts, x="Career Cluster", y="Employees",
            title="Employees by Career Cluster"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.pie(
            counts, names="Career Cluster", values="Employees",
            hole=0.45, title="Career Stage Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Career Cluster Summary")
    st.dataframe(counts, use_container_width=True, hide_index=True)

# ============================================================
# PROMOTION GAP
# ============================================================
elif page == "📈 Promotion Gap":

    st.header("📈 Promotion Gap Analysis")
    st.write(
        "Employees are grouped by the number of years since their last promotion "
        "to highlight potential career-progression gaps."
    )

    if not promotion_col:
        st.warning("No promotion-related column was detected.")
        st.stop()

    # Numeric promotion-gap field
    promotion_values = pd.to_numeric(df[promotion_col], errors="coerce")

    if promotion_values.notna().sum() == 0:
        st.warning("The detected promotion field is not numeric enough for gap analysis.")
        st.stop()

    work = df.copy()
    work["_promotion_years"] = promotion_values

    def gap_group(v):
        if pd.isna(v):
            return "Unknown"
        if v <= 2:
            return "0–2 years"
        if v <= 5:
            return "3–5 years"
        if v <= 10:
            return "6–10 years"
        return "10+ years"

    work["Promotion Gap"] = work["_promotion_years"].apply(gap_group)

    order = ["0–2 years", "3–5 years", "6–10 years", "10+ years", "Unknown"]
    gap_counts = (
        work["Promotion Gap"]
        .value_counts()
        .reindex(order)
        .dropna()
        .reset_index()
    )
    gap_counts.columns = ["Promotion Gap", "Employees"]

    c1, c2, c3 = st.columns(3)
    c1.metric("📌 Employees", f"{len(work):,}")
    c2.metric("⏳ Avg. Years Since Promotion",
              f"{work['_promotion_years'].mean():.1f}")
    c3.metric(
        "⚠️ 6+ Years Since Promotion",
        f"{(work['_promotion_years'].ge(6).mean() * 100):.1f}%"
    )

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        fig = px.bar(
            gap_counts,
            x="Promotion Gap",
            y="Employees",
            title="Employees by Promotion Gap"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.pie(
            gap_counts,
            names="Promotion Gap",
            values="Employees",
            hole=0.45,
            title="Promotion Gap Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    if department_col:
        st.subheader("🏢 Promotion Gap by Department")

        dept_gap = pd.crosstab(
            work[department_col],
            work["Promotion Gap"]
        ).reindex(columns=order, fill_value=0)

        st.dataframe(dept_gap, use_container_width=True)

        plot_df = dept_gap.reset_index().melt(
            id_vars=[department_col],
            var_name="Promotion Gap",
            value_name="Employees"
        )

        fig = px.bar(
            plot_df,
            x=department_col,
            y="Employees",
            color="Promotion Gap",
            barmode="group",
            title="Promotion Gap Distribution by Department"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Interpretation: a longer time since the last promotion does not by itself "
        "prove that an employee should be promoted. It is an indicator that can be "
        "reviewed alongside role, experience and performance information."
    )

# ============================================================
# RETENTION OPPORTUNITIES
# ============================================================
elif page == "🎯 Retention Opportunities":

    st.header("🎯 Retention Opportunities")
    st.write("Explore employee characteristics associated with retention and attrition.")

    if not attrition_col:
        st.warning("No attrition column was detected.")
        st.stop()

    status = df[attrition_col].astype(str).str.lower()
    df2 = df.copy()
    df2["Employee Status"] = np.where(
        status.isin(["yes", "true", "1", "left"]),
        "Attrition",
        "Retained"
    )

    summary = df2["Employee Status"].value_counts().reset_index()
    summary.columns = ["Status", "Employees"]

    attr_rate = (df2["Employee Status"].eq("Attrition").mean() * 100)

    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Employees", f"{len(df2):,}")
    c2.metric("🚪 Employees Leaving", f"{(df2['Employee Status'] == 'Attrition').sum():,}")
    c3.metric("📉 Attrition Rate", f"{attr_rate:.1f}%")

    left, right = st.columns(2)

    with left:
        fig = px.pie(
            summary, names="Status", values="Employees",
            hole=0.45, title="Retention vs Attrition"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.bar(
            summary, x="Status", y="Employees",
            title="Employee Status"
        )
        st.plotly_chart(fig, use_container_width=True)

    if department_col:
        st.subheader("🏢 Retention by Department")
        dept = pd.crosstab(df2[department_col], df2["Employee Status"]).reset_index()
        value_cols = [c for c in ["Retained", "Attrition"] if c in dept.columns]

        fig = px.bar(
            dept,
            x=department_col,
            y=value_cols,
            barmode="group",
            title="Retained vs Attrition by Department"
        )
        st.plotly_chart(fig, use_container_width=True)

    if job_role_col:
        st.subheader("💼 Attrition by Job Role")
        role = pd.crosstab(df2[job_role_col], df2["Employee Status"])
        if "Attrition" in role.columns:
            role["Attrition Rate (%)"] = (
                role["Attrition"] / role.sum(axis=1) * 100
            )
            role = role.sort_values("Attrition Rate (%)", ascending=False)

            fig = px.bar(
                role.reset_index().head(15),
                x="Attrition Rate (%)",
                y=job_role_col,
                orientation="h",
                title="Highest Attrition Rates by Job Role"
            )
            st.plotly_chart(fig, use_container_width=True)

    if overtime_col:
        st.subheader("⏰ Overtime and Attrition")
        ot = pd.crosstab(df2[overtime_col], df2["Employee Status"]).reset_index()
        st.dataframe(ot, use_container_width=True, hide_index=True)

# ============================================================
# EMPLOYEE EXPLORER
# ============================================================
elif page == "👤 Employee Explorer":

    st.header("👤 Employee Explorer")
    st.write("Filter the dataset and explore employee records.")

    filtered = df.copy()

    if department_col:
        vals = sorted(filtered[department_col].dropna().astype(str).unique())
        selected = st.multiselect("🏢 Department", vals)
        if selected:
            filtered = filtered[filtered[department_col].astype(str).isin(selected)]

    if gender_col:
        vals = sorted(filtered[gender_col].dropna().astype(str).unique())
        selected = st.multiselect("👥 Gender", vals)
        if selected:
            filtered = filtered[filtered[gender_col].astype(str).isin(selected)]

    if job_level_col:
        vals = sorted(filtered[job_level_col].dropna().astype(str).unique())
        selected = st.multiselect("💼 Job Level", vals)
        if selected:
            filtered = filtered[filtered[job_level_col].astype(str).isin(selected)]

    if attrition_col:
        vals = sorted(filtered[attrition_col].dropna().astype(str).unique())
        selected = st.multiselect("🚪 Attrition", vals)
        if selected:
            filtered = filtered[filtered[attrition_col].astype(str).isin(selected)]

    if experience_col and pd.api.types.is_numeric_dtype(df[experience_col]):
        min_v = int(df[experience_col].min())
        max_v = int(df[experience_col].max())
        if min_v < max_v:
            selected_range = st.slider(
                "💼 Years at Company",
                min_v, max_v, (min_v, max_v)
            )
            filtered = filtered[
                filtered[experience_col].between(
                    selected_range[0], selected_range[1]
                )
            ]

    st.markdown("---")

    c1, c2 = st.columns(2)
    c1.metric("Filtered Employees", f"{len(filtered):,}")
    c2.metric("Total Employees", f"{len(df):,}")

    st.subheader("Employee Records")
    st.dataframe(filtered, use_container_width=True, height=500)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    "Palo Alto Career Analytics | Python • Pandas • Plotly • Streamlit"
)
