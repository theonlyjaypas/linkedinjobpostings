
# NECESSARY IMPORTS
import os
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine, text

# DATABASE CONNECTION CONFIG [Reads from environment variables; falls back to localhost defaults if not set]
DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", "3306")),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "R3load24"),
    "database": os.getenv("MYSQL_DATABASE", "linkedin_jobs"),
}
_engine = None


# START MYSQL ENGINE [Returns a singleton SQLAlchemy engine; creates it on first call]
def get_engine():
    global _engine
    if _engine is None:
        cfg = DB_CONFIG
        url = (
            f"mysql+mysqlconnector://{cfg['user']}:{cfg['password']}"
            f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        )
        _engine = create_engine(url)
    return _engine


# PART 1: TOP SKILLS BY DEMAND [Ranks skills by how many distinct job postings require them]
def top_skills_by_demand(limit=15):
    sql = text("""
        SELECT sk.skill_name,
               COUNT(DISTINCT js.job_id) AS job_count
        FROM job_skills js
        JOIN skills sk ON js.skill_abr = sk.skill_abr
        GROUP BY sk.skill_name
        ORDER BY job_count DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 2: TOP SKILLS BY SALARY [Ranks skills by avg annual salary; filters outliers and low-sample skills]
def top_skills_by_salary(limit=15):
    sql = text("""
        SELECT sk.skill_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(DISTINCT js.job_id)           AS job_count
        FROM job_skills js
        JOIN skills  sk ON js.skill_abr  = sk.skill_abr
        JOIN salaries s  ON js.job_id    = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000  -- exclude unrealistic outliers
        GROUP BY sk.skill_name
        HAVING job_count >= 50                              -- minimum sample size for reliability
        ORDER BY avg_salary DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 3: TOP INDUSTRIES BY HIRING [Ranks industries by number of distinct job postings]
def top_industries_by_hiring(limit=15):
    sql = text("""
        SELECT i.industry_name,
               COUNT(DISTINCT ji.job_id) AS job_count
        FROM job_industries ji
        JOIN industries i ON ji.industry_id = i.industry_id
        GROUP BY i.industry_name
        ORDER BY job_count DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 4: TOP INDUSTRIES BY SALARY [Ranks industries by avg annual salary; requires min 30 postings]
def top_industries_by_salary(limit=15):
    sql = text("""
        SELECT i.industry_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(DISTINCT p.job_id)            AS job_count
        FROM postings p
        JOIN job_industries ji ON p.job_id      = ji.job_id
        JOIN industries     i  ON ji.industry_id = i.industry_id
        JOIN salaries       s  ON p.job_id       = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000  -- exclude unrealistic outliers
        GROUP BY i.industry_name
        HAVING job_count >= 30                              -- minimum sample size for reliability
        ORDER BY avg_salary DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 5: TOP COMPANIES BY HIRING [Ranks companies by total number of job postings]
def top_companies_by_hiring(limit=15):
    sql = text("""
        SELECT c.name AS company_name,
               COUNT(p.job_id) AS job_count
        FROM postings p
        JOIN companies c ON p.company_id = c.company_id
        GROUP BY c.name
        ORDER BY job_count DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 6: TOP COMPANIES BY SALARY [Ranks companies by avg annual salary; requires min 10 postings]
def top_companies_by_salary(limit=15):
    sql = text("""
        SELECT c.name AS company_name,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings  p
        JOIN companies c ON p.company_id = c.company_id
        JOIN salaries  s ON p.job_id     = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000  -- exclude unrealistic outliers
        GROUP BY c.name
        HAVING job_count >= 10                              -- minimum sample size for reliability
        ORDER BY avg_salary DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 7: SALARY BY EXPERIENCE LEVEL [Returns min/avg/max salary for each experience level]
def salary_by_experience():
    sql = text("""
        SELECT p.formatted_experience_level AS experience_level,
               ROUND(AVG(s.normalized_yearly), 0)  AS avg_salary,
               ROUND(MIN(s.normalized_yearly), 0)  AS min_salary,
               ROUND(MAX(s.normalized_yearly), 0)  AS max_salary,
               COUNT(p.job_id)                      AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
          AND p.formatted_experience_level != 'Unknown'  -- exclude rows with no level recorded
        GROUP BY p.formatted_experience_level
        ORDER BY avg_salary DESC
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn)


# PART 8: SALARY BY WORK TYPE [Compares avg salary across work types e.g. full-time, contract, part-time]
def salary_by_work_type():
    sql = text("""
        SELECT p.formatted_work_type AS work_type,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY p.formatted_work_type
        ORDER BY avg_salary DESC
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn)


# PART 9: TOP JOB TITLES BY SALARY [Ranks job titles by avg annual salary; requires min 10 postings]
def top_job_titles_by_salary(limit=15):
    sql = text("""
        SELECT p.title,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY p.title
        HAVING job_count >= 10                  -- minimum sample size for reliability
        ORDER BY avg_salary DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 10: BEST INDUSTRY + SKILL COMBINATIONS [Finds the highest-paying pairings of industry and skill]
def best_industry_skill_combos(limit=15):
    sql = text("""
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
        HAVING job_count >= 20                  -- minimum sample size for reliability
        ORDER BY avg_salary DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


# PART 11: REMOTE VS ON-SITE SALARY [Compares avg annual salary between remote and on-site roles]
def remote_vs_onsite_salary():
    sql = text("""
        SELECT CASE WHEN p.remote_allowed = 1 THEN 'Remote' ELSE 'On-site' END AS work_mode,
               ROUND(AVG(s.normalized_yearly), 0) AS avg_salary,
               COUNT(p.job_id)                     AS job_count
        FROM postings p
        JOIN salaries s ON p.job_id = s.job_id
        WHERE s.normalized_yearly IS NOT NULL
          AND s.normalized_yearly BETWEEN 20000 AND 500000
        GROUP BY work_mode
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn)


# PART 12: JOB SEARCH [Filters postings by keyword, skill, and/or industry; results sorted by salary descending]
def search_jobs(keyword="", skill="", industry="", limit=50):
    filters = []
    params = {"limit": limit}

    # Build WHERE clause dynamically based on which filters are provided
    if keyword:
        filters.append("p.title LIKE :keyword")
        params["keyword"] = f"%{keyword}%"
    if skill:
        # Subquery check — more efficient than a JOIN when filtering optionally
        filters.append("""
            EXISTS (
                SELECT 1 FROM job_skills js
                JOIN skills sk ON js.skill_abr = sk.skill_abr
                WHERE js.job_id = p.job_id AND sk.skill_name LIKE :skill
            )
        """)
        params["skill"] = f"%{skill}%"
    if industry:
        filters.append("""
            EXISTS (
                SELECT 1 FROM job_industries ji
                JOIN industries i ON ji.industry_id = i.industry_id
                WHERE ji.job_id = p.job_id AND i.industry_name LIKE :industry
            )
        """)
        params["industry"] = f"%{industry}%"

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = text(f"""
        SELECT p.job_id, p.title, c.name AS company_name,
               p.location, p.formatted_experience_level AS experience_level,
               p.formatted_work_type AS work_type,
               ROUND(s.normalized_yearly, 0) AS annual_salary
        FROM postings p
        LEFT JOIN companies c ON p.company_id = c.company_id
        LEFT JOIN salaries  s ON p.job_id     = s.job_id
        {where}
        ORDER BY s.normalized_yearly IS NULL, s.normalized_yearly DESC  -- nulls pushed to the bottom
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params=params)


# TEST BLOCK — Run all queries and print row counts to verify DB connection and data integrity
if __name__ == "__main__":
    queries = [
        ("PART 1  Top skills by demand",          top_skills_by_demand),
        ("PART 2  Top skills by salary",           top_skills_by_salary),
        ("PART 3  Top industries by hiring",       top_industries_by_hiring),
        ("PART 4  Top industries by salary",       top_industries_by_salary),
        ("PART 5  Top companies by hiring",        top_companies_by_hiring),
        ("PART 6  Top companies by salary",        top_companies_by_salary),
        ("PART 7  Salary by experience level",     salary_by_experience),
        ("PART 8  Salary by work type",            salary_by_work_type),
        ("PART 9  Top job titles by salary",       top_job_titles_by_salary),
        ("PART 10 Best industry+skill combos",     best_industry_skill_combos),
        ("PART 11 Remote vs on-site salary",       remote_vs_onsite_salary),
    ]

    for label, fn in queries:
        df = fn()
        print(f"\n{'='*55}")
        print(f"{label}  ({len(df)} rows)")
        print(df.to_string(index=False))

    print("\n\nPART 12 Job search — keyword='engineer', skill='Engineering'")
    print(search_jobs(keyword="engineer", skill="Engineering", limit=5).to_string(index=False))
