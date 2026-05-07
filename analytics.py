"""
analytics.py — Server-side analytics for LinkedIn Job Postings
All functions return a pandas DataFrame ready to send to the frontend.
"""

import sqlite3
import pandas as pd

DB_PATH = "linkedin_jobs.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Q1: Top skills by demand (# of job postings requiring that skill) ──────────
def top_skills_by_demand(limit=15):
    sql = """
        SELECT sk.skill_name,
               COUNT(DISTINCT js.job_id) AS job_count
        FROM job_skills js
        JOIN skills sk ON js.skill_abr = sk.skill_abr
        GROUP BY sk.skill_name
        ORDER BY job_count DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q2: Top skills by average annual salary ────────────────────────────────────
def top_skills_by_salary(limit=15):
    sql = """
        SELECT sk.skill_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(DISTINCT js.job_id)           AS job_count
        FROM job_skills js
        JOIN skills  sk ON js.skill_abr  = sk.skill_abr
        JOIN salaries s  ON js.job_id    = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY sk.skill_name
        HAVING job_count >= 50
        ORDER BY avg_salary DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q3: Top industries by hiring volume ────────────────────────────────────────
def top_industries_by_hiring(limit=15):
    sql = """
        SELECT i.industry_name,
               COUNT(DISTINCT ji.job_id) AS job_count
        FROM job_industries ji
        JOIN industries i ON ji.industry_id = i.industry_id
        GROUP BY i.industry_name
        ORDER BY job_count DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q4: Top industries by average annual salary ────────────────────────────────
def top_industries_by_salary(limit=15):
    sql = """
        SELECT i.industry_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(DISTINCT p.job_id)            AS job_count
        FROM postings p
        JOIN job_industries ji ON p.job_id      = ji.job_id
        JOIN industries     i  ON ji.industry_id = i.industry_id
        JOIN salaries       s  ON p.job_id       = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY i.industry_name
        HAVING job_count >= 30
        ORDER BY avg_salary DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q5: Top companies by hiring volume ─────────────────────────────────────────
def top_companies_by_hiring(limit=15):
    sql = """
        SELECT c.name AS company_name,
               COUNT(p.job_id) AS job_count
        FROM postings p
        JOIN companies c ON p.company_id = c.company_id
        GROUP BY c.name
        ORDER BY job_count DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q6: Top companies by average annual salary ─────────────────────────────────
def top_companies_by_salary(limit=15):
    sql = """
        SELECT c.name AS company_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings  p
        JOIN companies c ON p.company_id = c.company_id
        JOIN salaries  s ON p.job_id     = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY c.name
        HAVING job_count >= 10
        ORDER BY avg_salary DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q7: Salary distribution by experience level ────────────────────────────────
def salary_by_experience():
    sql = """
        SELECT p.formatted_experience_level AS experience_level,
               ROUND(AVG(s.normalized_yearly), 0)  AS avg_salary,
               ROUND(MIN(s.normalized_yearly), 0)  AS min_salary,
               ROUND(MAX(s.normalized_yearly), 0)  AS max_salary,
               COUNT(p.job_id)                      AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
          AND p.formatted_experience_level != 'Unknown'
        GROUP BY p.formatted_experience_level
        ORDER BY avg_salary DESC
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn)


# ── Q8: Salary distribution by work type ──────────────────────────────────────
def salary_by_work_type():
    sql = """
        SELECT p.formatted_work_type AS work_type,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY p.formatted_work_type
        ORDER BY avg_salary DESC
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn)


# ── Q9: Top job titles by average salary ──────────────────────────────────────
def top_job_titles_by_salary(limit=15):
    sql = """
        SELECT p.title,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY p.title
        HAVING job_count >= 10
        ORDER BY avg_salary DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q10: Best combinations — industry + skill by avg salary ───────────────────
def best_industry_skill_combos(limit=15):
    sql = """
        SELECT i.industry_name,
               sk.skill_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(DISTINCT p.job_id)            AS job_count
        FROM postings     p
        JOIN job_industries ji ON p.job_id       = ji.job_id
        JOIN industries    i   ON ji.industry_id  = i.industry_id
        JOIN job_skills    js  ON p.job_id        = js.job_id
        JOIN skills        sk  ON js.skill_abr    = sk.skill_abr
        JOIN salaries      s   ON p.job_id        = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY i.industry_name, sk.skill_name
        HAVING job_count >= 20
        ORDER BY avg_salary DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=(limit,))


# ── Q11: Remote vs on-site salary comparison ──────────────────────────────────
def remote_vs_onsite_salary():
    sql = """
        SELECT CASE WHEN p.remote_allowed = 1 THEN 'Remote' ELSE 'On-site' END AS work_mode,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY work_mode
    """
    with get_conn() as conn:
        return pd.read_sql(sql, conn)


# ── Q12: Job search — filter postings by keyword / skill / industry ────────────
def search_jobs(keyword="", skill="", industry="", limit=50):
    params = []
    filters = []

    if keyword:
        filters.append("p.title LIKE ?")
        params.append(f"%{keyword}%")
    if skill:
        filters.append("""
            EXISTS (
                SELECT 1 FROM job_skills js
                JOIN skills sk ON js.skill_abr = sk.skill_abr
                WHERE js.job_id = p.job_id AND sk.skill_name LIKE ?
            )
        """)
        params.append(f"%{skill}%")
    if industry:
        filters.append("""
            EXISTS (
                SELECT 1 FROM job_industries ji
                JOIN industries i ON ji.industry_id = i.industry_id
                WHERE ji.job_id = p.job_id AND i.industry_name LIKE ?
            )
        """)
        params.append(f"%{industry}%")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = f"""
        SELECT p.job_id, p.title, c.name AS company_name,
               p.location, p.formatted_experience_level AS experience_level,
               p.formatted_work_type AS work_type,
               ROUND(s.normalized_yearly, 0) AS annual_salary
        FROM postings p
        LEFT JOIN companies c ON p.company_id = c.company_id
        LEFT JOIN salaries  s ON p.job_id     = s.job_id
        {where}
        ORDER BY s.normalized_yearly DESC NULLS LAST
        LIMIT ?
    """
    params.append(limit)
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=params)


# ── Quick test — run all queries and print row counts ─────────────────────────
if __name__ == "__main__":
    queries = [
        ("Q1  Top skills by demand",          top_skills_by_demand),
        ("Q2  Top skills by salary",           top_skills_by_salary),
        ("Q3  Top industries by hiring",       top_industries_by_hiring),
        ("Q4  Top industries by salary",       top_industries_by_salary),
        ("Q5  Top companies by hiring",        top_companies_by_hiring),
        ("Q6  Top companies by salary",        top_companies_by_salary),
        ("Q7  Salary by experience level",     salary_by_experience),
        ("Q8  Salary by work type",            salary_by_work_type),
        ("Q9  Top job titles by salary",       top_job_titles_by_salary),
        ("Q10 Best industry+skill combos",     best_industry_skill_combos),
        ("Q11 Remote vs on-site salary",       remote_vs_onsite_salary),
    ]

    for label, fn in queries:
        df = fn()
        print(f"\n{'='*55}")
        print(f"{label}  ({len(df)} rows)")
        print(df.to_string(index=False))

    print("\n\nQ12 Job search — keyword='engineer', skill='Engineering'")
    print(search_jobs(keyword="engineer", skill="Engineering", limit=5).to_string(index=False))
