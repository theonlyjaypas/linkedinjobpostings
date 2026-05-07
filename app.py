"""
DATA 201 Group 2 — LinkedIn Job Postings Dashboard
Streamlit web application with server-side analytics and Plotly charts.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from analytics import (
    top_skills_by_demand, top_skills_by_salary,
    top_industries_by_hiring, top_industries_by_salary,
    top_companies_by_hiring, top_companies_by_salary,
    salary_by_experience, salary_by_work_type,
    top_job_titles_by_salary, best_industry_skill_combos,
    remote_vs_onsite_salary, search_jobs,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LinkedIn Jobs Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS — Inter font + polished component styles ────────────────────────
st.markdown("""
<style>
html, body, [class*="css"], .stMarkdown, .stText, button, input, select, textarea {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important;
}

/* Sidebar shell */
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.06);
    padding-top: 2rem;
    min-width: 200px;
}

/* Sidebar brand title */
section[data-testid="stSidebar"] h3 {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    color: #fff !important;
    margin-bottom: 0.1rem !important;
    padding-left: 1rem;
}

/* "Navigate" radio group label — hidden, section divider only */
.stRadio > label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555;
    padding-left: 1rem;
    margin-bottom: 0.5rem;
    margin-top: 0.75rem;
}

/* Nav item row — hide the radio circle entirely */
.stRadio > div { gap: 0; flex-direction: column; }
.stRadio > div > label > div:first-child { display: none !important; }

/* Nav item label */
.stRadio > div > label {
    display: flex;
    align-items: center;
    padding: 0.55rem 0.75rem 0.55rem 1rem;
    margin: 1px 0.75rem;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #aaa;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.stRadio > div > label:hover {
    background: rgba(255,255,255,0.05);
    color: #fff;
}

/* Active nav item — blue left accent */
.stRadio > div > label:has(input:checked) {
    background: rgba(10,102,194,0.15);
    border-left: 3px solid #0A66C2;
    color: #fff;
    font-weight: 600;
    margin: 1px 0.75rem;
}

/* KPI metric cards */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 1.1rem 1.4rem 1rem;
}
[data-testid="metric-container"] > div:first-child {
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #999;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 700;
}

/* Page title */
h1 { font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
h2 { font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; }
h3 { font-weight: 600; letter-spacing: 0.02em; text-transform: uppercase; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.08); }
.stTabs [data-baseweb="tab"] { font-size: 0.88rem; font-weight: 500; padding: 0.5rem 1rem; border-radius: 8px 8px 0 0; }

/* Divider */
hr { border-color: rgba(255,255,255,0.07) !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.markdown("### LinkedIn Jobs")
st.sidebar.caption("DATA 201 · Group 2")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Skills", "Industries", "Companies", "Salary Insights", "Job Search"],
)
st.sidebar.markdown("---")
st.sidebar.caption("LinkedIn Job Postings 2023–2024  \n~124K postings · 11 CSV files")

# ── Colour palette ─────────────────────────────────────────────────────────────
BLUE   = "#0A66C2"   # LinkedIn blue
TEAL   = "#00BFA5"
ORANGE = "#FF6B35"
PURPLE = "#7C4DFF"


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("LinkedIn Job Market — Overview")
    st.caption("This dashboard analyzes 123,849 LinkedIn job postings collected between 2023 and 2024 across 24,473 companies and 388 industries. It surfaces trends in hiring demand, salary expectations, and the skills employers value most. Use the sidebar to explore deeper breakdowns by skill, industry, company, or experience level.")

    # ── Fetch data once ────────────────────────────────────────────────────────
    df_skills     = top_skills_by_demand(10)
    df_industries = top_industries_by_hiring(10)
    df_remote     = remote_vs_onsite_salary()
    df_exp        = salary_by_experience()
    order = ["Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
    df_exp = df_exp[df_exp["experience_level"].isin(order)]
    df_exp["experience_level"] = pd.Categorical(df_exp["experience_level"], categories=order, ordered=True)
    df_exp = df_exp.sort_values("experience_level")
    delta = int(df_remote[df_remote["work_mode"] == "Remote"]["avg_salary"].values[0] -
                df_remote[df_remote["work_mode"] == "On-site"]["avg_salary"].values[0])

    # ── KPI cards ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Postings", "123,849")
    col2.metric("Companies", "24,473")
    col3.metric("Industries", "388")
    col4.metric("Unique Skills", "35")

    st.markdown("---")

    # ── Insight callouts ───────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Most in-demand skill:** {df_skills.iloc[0]['skill_name']} — {df_skills.iloc[0]['job_count']:,} postings")
    c2.info(f"**Top hiring industry:** {df_industries.iloc[0]['industry_name']} — {df_industries.iloc[0]['job_count']:,} postings")
    c3.info(f"**Remote pay premium:** ${delta:,} more per year than on-site")

    st.markdown("---")

    # ── Row 1: Skills (left) + Industries (right) ──────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Most In-Demand Skills")
        fig = px.bar(
            df_skills, x="job_count", y="skill_name", orientation="h",
            text="job_count",
            labels={"job_count": "Job Postings", "skill_name": ""},
        )
        fig.update_traces(marker_color=BLUE, textposition="outside", textfont_size=10)
        fig.update_layout(
            height=400,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Job Postings",
            margin=dict(t=20, r=60, b=20, l=10),
        )
        st.plotly_chart(fig)

    with col_right:
        st.subheader("Top Hiring Industries")
        fig = px.bar(
            df_industries, x="job_count", y="industry_name", orientation="h",
            text="job_count",
            labels={"job_count": "Job Postings", "industry_name": ""},
        )
        fig.update_traces(marker_color=TEAL, textposition="outside", textfont_size=10)
        fig.update_layout(
            height=400,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Job Postings",
            margin=dict(t=20, r=60, b=20, l=10),
        )
        st.plotly_chart(fig)

    st.markdown("---")

    # ── Row 2: Remote vs on-site (left) + Experience salary (right) ───────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Remote vs On-Site Salary")
        fig = px.bar(
            df_remote, x="work_mode", y="avg_salary",
            color="work_mode", color_discrete_map={"Remote": TEAL, "On-site": BLUE},
            text=df_remote["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "work_mode": ""},
        )
        fig.update_traces(textposition="outside", textfont_size=13)
        fig.update_layout(
            showlegend=False, height=380,
            yaxis_tickprefix="$", yaxis_tickformat=",",
            yaxis_range=[0, df_remote["avg_salary"].max() * 1.22],
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig)

    with col_right2:
        st.subheader("Salary by Experience Level")
        fig = px.bar(
            df_exp, x="experience_level", y="avg_salary",
            text=df_exp["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "experience_level": ""},
        )
        fig.update_traces(marker_color=ORANGE, textposition="outside", textfont_size=11)
        fig.update_layout(
            height=380,
            yaxis_tickprefix="$", yaxis_tickformat=",",
            yaxis_range=[0, df_exp["avg_salary"].max() * 1.22],
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SKILLS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Skills":
    st.title("Skills Analysis")
    st.caption("Skills are one of the strongest signals of what employers are actively looking for in the job market. This page breaks down which skills appear most frequently across all 123,849 postings and which ones are associated with the highest average annual salaries. The bubble chart reveals how demand and pay interact — helping identify skills that are both sought-after and well-compensated.")

    limit = st.slider("Number of skills to display", 5, 35, 15)

    # ── Fetch data once ────────────────────────────────────────────────────────
    df_demand = top_skills_by_demand(limit)
    df_salary = top_skills_by_salary(limit)

    # ── Insight callout row ────────────────────────────────────────────────────
    top_demand = df_demand.iloc[0]
    top_pay    = df_salary.iloc[0]
    c1, c2 = st.columns(2)
    c1.info(f"**Most in-demand skill:** {top_demand['skill_name']} — {top_demand['job_count']:,} postings")
    c2.info(f"**Highest paying skill:** {top_pay['skill_name']} — ${top_pay['avg_salary']:,.0f} avg/yr")

    st.markdown("---")

    # ── Two-column layout — demand left, salary right ──────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Most In-Demand Skills")
        fig = px.bar(
            df_demand, x="job_count", y="skill_name", orientation="h",
            text="job_count",
            labels={"job_count": "Job Postings", "skill_name": ""},
        )
        fig.update_traces(
            marker_color=BLUE,
            textposition="outside",
            textfont_size=11,
        )
        fig.update_layout(
            height=480,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Job Postings",
            margin=dict(t=20, r=60, b=20, l=10),
        )
        st.plotly_chart(fig)

        with st.expander("View data table"):
            st.dataframe(df_demand, hide_index=True)

    with col_right:
        st.subheader("Highest Paying Skills")
        fig = px.bar(
            df_salary, x="avg_salary", y="skill_name", orientation="h",
            text=df_salary["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "skill_name": ""},
        )
        fig.update_traces(
            marker_color=ORANGE,
            textposition="outside",
            textfont_size=11,
        )
        fig.update_layout(
            height=480,
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickprefix="$", xaxis_tickformat=",",
            xaxis_range=[0, df_salary["avg_salary"].max() * 1.25],
            margin=dict(t=20, r=80, b=20, l=10),
        )
        st.plotly_chart(fig)

        with st.expander("View data table"):
            st.dataframe(df_salary, hide_index=True)

    st.markdown("---")

    # ── Bubble chart — salary vs demand ───────────────────────────────────────
    st.subheader("Salary vs Demand")
    fig_bubble = px.scatter(
        df_salary,
        x="job_count", y="avg_salary",
        size="job_count",
        color="skill_name",
        text="skill_name",
        labels={"avg_salary": "Avg Annual Salary ($)", "job_count": "Number of Postings", "skill_name": "Skill"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_bubble.update_traces(
        textposition="top center",
        textfont_size=11,
        marker=dict(opacity=0.85, line=dict(width=1, color="rgba(255,255,255,0.2)")),
    )
    fig_bubble.update_layout(
        height=460,
        showlegend=False,
        yaxis_tickprefix="$", yaxis_tickformat=",",
        xaxis_title="Number of Job Postings",
        yaxis_title="Avg Annual Salary ($)",
        margin=dict(t=30, b=40),
    )
    st.plotly_chart(fig_bubble)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — INDUSTRIES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Industries":
    st.title("Industry Analysis")
    st.caption("Different industries vary widely in both the volume of jobs they post and the salaries they offer. This page compares 388 industries across hiring activity and average annual compensation, revealing which sectors are growing fastest and which offer the strongest pay. The combination chart at the bottom pinpoints the most lucrative industry and skill pairings in the dataset.")

    limit = st.slider("Number of industries to display", 5, 30, 15)

    # ── Fetch data once ────────────────────────────────────────────────────────
    df_hiring = top_industries_by_hiring(limit)
    df_salary = top_industries_by_salary(limit)

    # ── Insight callouts ───────────────────────────────────────────────────────
    top_hiring = df_hiring.iloc[0]
    top_pay    = df_salary.iloc[0]
    c1, c2 = st.columns(2)
    c1.info(f"**Most hiring industry:** {top_hiring['industry_name']} — {top_hiring['job_count']:,} postings")
    c2.info(f"**Highest paying industry:** {top_pay['industry_name']} — ${top_pay['avg_salary']:,.0f} avg/yr")

    st.markdown("---")

    # ── Two-column layout ──────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Hiring Volume")
        fig = px.bar(
            df_hiring, x="job_count", y="industry_name", orientation="h",
            text="job_count",
            labels={"job_count": "Job Postings", "industry_name": ""},
        )
        fig.update_traces(
            marker_color=TEAL,
            textposition="outside",
            textfont_size=10,
        )
        fig.update_layout(
            height=500,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Job Postings",
            margin=dict(t=20, r=70, b=20, l=10),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_hiring, hide_index=True)

    with col_right:
        st.subheader("Average Annual Salary")
        fig = px.bar(
            df_salary, x="avg_salary", y="industry_name", orientation="h",
            text=df_salary["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "industry_name": ""},
        )
        fig.update_traces(
            marker_color=ORANGE,
            textposition="outside",
            textfont_size=10,
        )
        fig.update_layout(
            height=500,
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickprefix="$", xaxis_tickformat=",",
            xaxis_range=[0, df_salary["avg_salary"].max() * 1.28],
            margin=dict(t=20, r=90, b=20, l=10),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_salary, hide_index=True)

    st.markdown("---")

    # ── Best combos — full width ranked bar ───────────────────────────────────
    st.subheader("Best Industry + Skill Combinations")
    st.caption("Top pairings ranked by average annual salary — each bar is one industry + skill combination.")
    df_combo = best_industry_skill_combos(15)
    df_combo["combo"] = df_combo["industry_name"] + "  ·  " + df_combo["skill_name"]
    df_combo = df_combo.sort_values("avg_salary", ascending=True)
    fig_combo = px.bar(
        df_combo, x="avg_salary", y="combo", orientation="h",
        text=df_combo["avg_salary"].apply(lambda v: f"${v:,.0f}"),
        labels={"avg_salary": "Avg Annual Salary ($)", "combo": ""},
    )
    fig_combo.update_traces(
        marker_color=PURPLE,
        textposition="outside",
        textfont_size=11,
    )
    fig_combo.update_layout(
        height=520,
        xaxis_tickprefix="$", xaxis_tickformat=",",
        xaxis_range=[0, df_combo["avg_salary"].max() * 1.28],
        margin=dict(t=20, r=100, b=20, l=10),
    )
    st.plotly_chart(fig_combo)
    with st.expander("View data table"):
        st.dataframe(df_combo[["industry_name", "skill_name", "avg_salary", "job_count"]], hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — COMPANIES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Companies":
    st.title("Company Analysis")
    st.caption("With over 24,000 companies represented in this dataset, the job market is shaped by a mix of large-scale hirers and high-paying specialists. This page identifies which companies are posting the most jobs and which are offering the highest average salaries — two metrics that don't always align. Companies with fewer postings but higher pay often reflect specialized or senior-heavy roles.")

    limit = st.slider("Number of companies to display", 5, 25, 15)

    # ── Fetch data once ────────────────────────────────────────────────────────
    df_hiring = top_companies_by_hiring(limit)
    df_salary = top_companies_by_salary(limit)

    # ── Insight callouts ───────────────────────────────────────────────────────
    top_hiring = df_hiring.iloc[0]
    top_pay    = df_salary.iloc[0]
    c1, c2 = st.columns(2)
    c1.info(f"**Most hiring company:** {top_hiring['company_name']} — {top_hiring['job_count']:,} postings")
    c2.info(f"**Highest paying company:** {top_pay['company_name']} — ${top_pay['avg_salary']:,.0f} avg/yr")

    st.markdown("---")

    # ── Two-column layout ──────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Hiring Volume")
        fig = px.bar(
            df_hiring, x="job_count", y="company_name", orientation="h",
            text="job_count",
            labels={"job_count": "Job Postings", "company_name": ""},
        )
        fig.update_traces(
            marker_color=BLUE,
            textposition="outside",
            textfont_size=10,
        )
        fig.update_layout(
            height=520,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Job Postings",
            margin=dict(t=20, r=70, b=20, l=10),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_hiring, hide_index=True)

    with col_right:
        st.subheader("Average Annual Salary")
        fig = px.bar(
            df_salary, x="avg_salary", y="company_name", orientation="h",
            text=df_salary["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "company_name": ""},
        )
        fig.update_traces(
            marker_color=ORANGE,
            textposition="outside",
            textfont_size=10,
        )
        fig.update_layout(
            height=520,
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickprefix="$", xaxis_tickformat=",",
            xaxis_range=[0, df_salary["avg_salary"].max() * 1.28],
            margin=dict(t=20, r=100, b=20, l=10),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_salary, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — SALARY INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Salary Insights":
    st.title("Salary Insights")
    st.caption("Salary in the job market is shaped by multiple factors — experience level, work arrangement, job title, and whether a role is remote or on-site. This page breaks down how each of these variables influences annual compensation across the dataset. Together, these views help identify where the highest-paying opportunities are concentrated and what attributes consistently drive salary upward.")

    # ── Fetch data once ────────────────────────────────────────────────────────
    df_exp     = salary_by_experience()
    df_wtype   = salary_by_work_type()
    df_remote  = remote_vs_onsite_salary()
    df_titles  = top_job_titles_by_salary(15)

    order = ["Entry level", "Internship", "Associate", "Mid-Senior level", "Director", "Executive"]
    df_exp = df_exp[df_exp["experience_level"].isin(order)]
    df_exp["experience_level"] = pd.Categorical(df_exp["experience_level"], categories=order, ordered=True)
    df_exp = df_exp.sort_values("experience_level")

    delta = int(df_remote[df_remote["work_mode"] == "Remote"]["avg_salary"].values[0] -
                df_remote[df_remote["work_mode"] == "On-site"]["avg_salary"].values[0])
    top_title = df_titles.iloc[0]

    # ── Insight callouts ───────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Top experience level:** Executive — ${df_exp[df_exp['experience_level']=='Executive']['avg_salary'].values[0]:,.0f} avg/yr")
    c2.info(f"**Remote pay premium:** ${delta:,} more per year than on-site")
    c3.info(f"**Top job title:** {top_title['title']} — ${top_title['avg_salary']:,.0f} avg/yr")

    st.markdown("---")

    # ── Row 1: Experience level (left) + Work type (right) ────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Salary by Experience Level")
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Min", x=df_exp["experience_level"], y=df_exp["min_salary"], marker_color="#4A5568"))
        fig.add_trace(go.Bar(name="Avg", x=df_exp["experience_level"], y=df_exp["avg_salary"], marker_color=BLUE))
        fig.add_trace(go.Bar(name="Max", x=df_exp["experience_level"], y=df_exp["max_salary"], marker_color=ORANGE))
        fig.update_layout(
            barmode="group", height=400,
            yaxis_tickprefix="$", yaxis_tickformat=",",
            yaxis_title="Annual Salary ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_exp, hide_index=True)

    with col_right:
        st.subheader("Salary by Work Type")
        fig = px.bar(
            df_wtype, x="work_type", y="avg_salary",
            text=df_wtype["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "work_type": ""},
        )
        fig.update_traces(marker_color=PURPLE, textposition="outside", textfont_size=11)
        fig.update_layout(
            height=400,
            yaxis_tickprefix="$", yaxis_tickformat=",",
            yaxis_range=[0, df_wtype["avg_salary"].max() * 1.22],
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_wtype, hide_index=True)

    st.markdown("---")

    # ── Row 2: Remote vs on-site (left) + Top job titles (right) ─────────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Remote vs On-Site")
        fig = px.bar(
            df_remote, x="work_mode", y="avg_salary",
            color="work_mode", color_discrete_map={"Remote": TEAL, "On-site": BLUE},
            text=df_remote["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "work_mode": ""},
        )
        fig.update_traces(textposition="outside", textfont_size=13)
        fig.update_layout(
            showlegend=False, height=400,
            yaxis_tickprefix="$", yaxis_tickformat=",",
            yaxis_range=[0, df_remote["avg_salary"].max() * 1.22],
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_remote, hide_index=True)

    with col_right2:
        st.subheader("Top Job Titles by Salary")
        fig = px.bar(
            df_titles, x="avg_salary", y="title", orientation="h",
            text=df_titles["avg_salary"].apply(lambda v: f"${v:,.0f}"),
            labels={"avg_salary": "Avg Annual Salary ($)", "title": ""},
        )
        fig.update_traces(marker_color=ORANGE, textposition="outside", textfont_size=10)
        fig.update_layout(
            height=400,
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickprefix="$", xaxis_tickformat=",",
            xaxis_range=[0, df_titles["avg_salary"].max() * 1.28],
            margin=dict(t=20, r=100, b=20, l=10),
        )
        st.plotly_chart(fig)
        with st.expander("View data table"):
            st.dataframe(df_titles, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — JOB SEARCH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Job Search":
    st.title("Job Search")
    st.caption("Search across all 123,849 job postings using any combination of job title keyword, skill, or industry. Results are ranked by annual salary so the highest-paying matches surface first. The charts below each search update dynamically to show the salary distribution and top companies within your filtered results.")

    st.markdown("---")

    # ── Search controls ────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    keyword  = col1.text_input("Job Title", placeholder="e.g. Data Scientist")
    skill    = col2.text_input("Skill", placeholder="e.g. Engineering")
    industry = col3.text_input("Industry", placeholder="e.g. Software")
    limit    = col4.number_input("Max", min_value=10, max_value=200, value=50, step=10)

    search_clicked = st.button("Search", type="primary")

    if search_clicked or keyword or skill or industry:
        df = search_jobs(keyword=keyword, skill=skill, industry=industry, limit=limit)

        st.markdown("---")

        if df.empty:
            st.warning("No results found. Try broader search terms.")
        else:
            has_salary = df["annual_salary"].notna()
            salary_df  = df[has_salary & (df["annual_salary"] <= 500000)].copy()

            # ── Insight callouts ───────────────────────────────────────────────
            c1, c2, c3 = st.columns(3)
            c1.metric("Results Found", f"{len(df):,}")
            if has_salary.any():
                c2.metric("Avg Salary", f"${df.loc[has_salary, 'annual_salary'].mean():,.0f}")
                c3.metric("Max Salary", f"${df.loc[has_salary, 'annual_salary'].max():,.0f}")

            st.markdown("---")

            # ── Charts: distribution (left) + top companies in results (right) ─
            if not salary_df.empty:
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader("Salary Distribution")
                    fig = px.histogram(
                        salary_df, x="annual_salary", nbins=25,
                        labels={"annual_salary": "Annual Salary ($)", "count": "Postings"},
                    )
                    fig.update_traces(marker_color=BLUE, marker_line_width=0)
                    fig.update_layout(
                        height=340,
                        xaxis_tickprefix="$", xaxis_tickformat=",",
                        bargap=0.05,
                        margin=dict(t=30, b=20),
                    )
                    st.plotly_chart(fig)

                with col_right:
                    st.subheader("Top Companies in Results")
                    top_cos = (
                        df.dropna(subset=["company_name"])
                        .groupby("company_name")
                        .size()
                        .reset_index(name="count")
                        .sort_values("count", ascending=True)
                        .tail(10)
                    )
                    fig2 = px.bar(
                        top_cos, x="count", y="company_name", orientation="h",
                        text="count",
                        labels={"count": "Postings", "company_name": ""},
                    )
                    fig2.update_traces(marker_color=TEAL, textposition="outside", textfont_size=10)
                    fig2.update_layout(
                        height=340,
                        margin=dict(t=30, r=50, b=20, l=10),
                    )
                    st.plotly_chart(fig2)

            st.markdown("---")

            # ── Results table ──────────────────────────────────────────────────
            st.subheader(f"All Results  —  {len(df):,} postings")
            st.dataframe(
                df.rename(columns={
                    "job_id": "Job ID", "title": "Title",
                    "company_name": "Company", "location": "Location",
                    "experience_level": "Experience", "work_type": "Work Type",
                    "annual_salary": "Annual Salary ($)",
                }),
                hide_index=True,
            )
