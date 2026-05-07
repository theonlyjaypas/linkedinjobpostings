"""
ETL script — LinkedIn Job Postings (2023-2024)
Loads and cleans all 11 CSV files into a MySQL database.

Configure connection via environment variables (or edit DB_CONFIG defaults):
  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text, event, VARCHAR

DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", "3306")),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "R3load24"),
    "database": os.getenv("MYSQL_DATABASE", "linkedin_jobs"),
}

PERIOD_TO_YEARLY = {
    "HOURLY":   2080,
    "WEEKLY":   52,
    "BIWEEKLY": 26,
    "MONTHLY":  12,
    "YEARLY":   1,
}


def normalize_yearly(row):
    multiplier = PERIOD_TO_YEARLY.get(str(row.get("pay_period", "")).upper(), None)
    if multiplier is None:
        return None
    val = row.get("max_salary") or row.get("med_salary") or row.get("min_salary")
    if pd.isna(val) or val is None:
        return None
    return round(float(val) * multiplier, 2)


def load_csv(path):
    return pd.read_csv(path, low_memory=False)


def get_engine():
    cfg = DB_CONFIG
    url = (
        f"mysql+mysqlconnector://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
    engine = create_engine(url)

    # Disable FK checks on every connection so loads never block on constraints
    @event.listens_for(engine, "connect")
    def set_fk_checks(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.close()

    return engine


def run_etl():
    engine = get_engine()

    # Drop all existing objects in reverse dependency order
    with engine.connect() as conn:
        for obj, kind in [
            ("analytics",          "VIEW"),
            ("benefits",           "TABLE"),
            ("job_skills",         "TABLE"),
            ("job_industries",     "TABLE"),
            ("salaries",           "TABLE"),
            ("postings",           "TABLE"),
            ("employee_counts",    "TABLE"),
            ("company_industries", "TABLE"),
            ("companies",          "TABLE"),
            ("skills",             "TABLE"),
            ("industries",         "TABLE"),
        ]:
            conn.execute(text(f"DROP {kind} IF EXISTS `{obj}`"))
        conn.commit()

    print("Dropped existing tables.")

    # ------------------------------------------------------------------
    # 1. industries
    # ------------------------------------------------------------------
    df = load_csv("mappings/industries.csv")
    df = df.dropna(subset=["industry_name"])
    df.to_sql("industries", engine, if_exists="replace", index=False)
    print(f"industries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 2. skills
    # ------------------------------------------------------------------
    df = load_csv("mappings/skills.csv")
    df = df.dropna(subset=["skill_name"])
    df.to_sql("skills", engine, if_exists="replace", index=False,
              dtype={"skill_abr": VARCHAR(50)})
    print(f"skills: {len(df)} rows")

    # ------------------------------------------------------------------
    # 3. companies
    # ------------------------------------------------------------------
    df = load_csv("companies/companies.csv")
    df = df[["company_id", "name", "company_size", "state", "country", "city", "url"]]
    df = df.dropna(subset=["company_id"])
    df["company_id"] = df["company_id"].astype(int)
    df.to_sql("companies", engine, if_exists="replace", index=False)
    print(f"companies: {len(df)} rows")

    # ------------------------------------------------------------------
    # 4. company_industries
    # ------------------------------------------------------------------
    df = load_csv("companies/company_industries.csv")
    ind_map = pd.read_sql("SELECT industry_id, industry_name FROM industries", engine)
    ind_name_to_id = dict(zip(ind_map["industry_name"], ind_map["industry_id"]))
    df["industry_id"] = df["industry"].map(ind_name_to_id)
    df = df.dropna(subset=["company_id", "industry_id"])
    df["company_id"] = df["company_id"].astype(int)
    df["industry_id"] = df["industry_id"].astype(int)
    df = df[["company_id", "industry_id"]].drop_duplicates()
    df.to_sql("company_industries", engine, if_exists="replace", index=False)
    print(f"company_industries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 5. employee_counts
    # ------------------------------------------------------------------
    df = load_csv("companies/employee_counts.csv")
    df = df.dropna(subset=["company_id"])
    df["company_id"] = df["company_id"].astype(int)
    df = df.sort_values("time_recorded", ascending=False).drop_duplicates(subset=["company_id"])
    df = df[["company_id", "employee_count", "follower_count", "time_recorded"]]
    df.to_sql("employee_counts", engine, if_exists="replace", index=False)
    print(f"employee_counts: {len(df)} rows")

    # ------------------------------------------------------------------
    # 6. postings
    # ------------------------------------------------------------------
    df = load_csv("postings.csv")
    keep = [
        "job_id", "company_id", "title", "location",
        "formatted_work_type", "formatted_experience_level",
        "remote_allowed", "listed_time"
    ]
    df = df[keep].copy()
    df = df.dropna(subset=["job_id"])
    df["job_id"] = df["job_id"].astype(int)
    df["company_id"] = pd.to_numeric(df["company_id"], errors="coerce")
    df["company_id"] = df["company_id"].where(df["company_id"].notna(), other=None)
    df["formatted_experience_level"] = df["formatted_experience_level"].fillna("Unknown")
    df["remote_allowed"] = df["remote_allowed"].fillna(0).astype(int)
    df.to_sql("postings", engine, if_exists="replace", index=False)
    print(f"postings: {len(df)} rows")

    # ------------------------------------------------------------------
    # 7. salaries
    # ------------------------------------------------------------------
    df = load_csv("jobs/salaries.csv")
    df = df.dropna(subset=["job_id"])
    df["job_id"] = df["job_id"].astype(int)
    df["normalized_yearly"] = df.apply(normalize_yearly, axis=1)
    df = df[["salary_id", "job_id", "min_salary", "med_salary", "max_salary",
             "pay_period", "currency", "compensation_type", "normalized_yearly"]]
    df.to_sql("salaries", engine, if_exists="replace", index=False)
    print(f"salaries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 8. job_skills
    # ------------------------------------------------------------------
    df = load_csv("jobs/job_skills.csv")
    df = df.dropna(subset=["job_id", "skill_abr"])
    df["job_id"] = df["job_id"].astype(int)
    valid_skills = set(pd.read_sql("SELECT skill_abr FROM skills", engine)["skill_abr"])
    df = df[df["skill_abr"].isin(valid_skills)]
    df = df.drop_duplicates()
    df.to_sql("job_skills", engine, if_exists="replace", index=False,
              dtype={"skill_abr": VARCHAR(50)})
    print(f"job_skills: {len(df)} rows")

    # ------------------------------------------------------------------
    # 9. job_industries
    # ------------------------------------------------------------------
    df = load_csv("jobs/job_industries.csv")
    df = df.dropna(subset=["job_id", "industry_id"])
    df["job_id"] = df["job_id"].astype(int)
    df["industry_id"] = df["industry_id"].astype(int)
    valid_ind = set(pd.read_sql("SELECT industry_id FROM industries", engine)["industry_id"])
    df = df[df["industry_id"].isin(valid_ind)]
    df = df.drop_duplicates()
    df.to_sql("job_industries", engine, if_exists="replace", index=False)
    print(f"job_industries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 10. benefits
    # ------------------------------------------------------------------
    df = load_csv("jobs/benefits.csv")
    df = df.dropna(subset=["job_id", "type"])
    df["job_id"] = df["job_id"].astype(int)
    df["inferred"] = df["inferred"].fillna(0).astype(int)
    df = df.drop_duplicates(subset=["job_id", "type"])
    df.to_sql("benefits", engine, if_exists="replace", index=False,
              dtype={"type": VARCHAR(100)})
    print(f"benefits: {len(df)} rows")

    # ------------------------------------------------------------------
    # Add primary keys for query performance
    # ------------------------------------------------------------------
    print("Adding primary keys...")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE industries ADD PRIMARY KEY (industry_id)"))
        conn.execute(text("ALTER TABLE skills ADD PRIMARY KEY (skill_abr)"))
        conn.execute(text("ALTER TABLE companies ADD PRIMARY KEY (company_id)"))
        conn.execute(text("ALTER TABLE company_industries ADD PRIMARY KEY (company_id, industry_id)"))
        conn.execute(text("ALTER TABLE employee_counts ADD PRIMARY KEY (company_id)"))
        conn.execute(text("ALTER TABLE postings ADD PRIMARY KEY (job_id)"))
        conn.execute(text("ALTER TABLE salaries ADD PRIMARY KEY (salary_id)"))
        conn.execute(text("ALTER TABLE job_skills ADD PRIMARY KEY (job_id, skill_abr)"))
        conn.execute(text("ALTER TABLE job_industries ADD PRIMARY KEY (job_id, industry_id)"))
        conn.execute(text("ALTER TABLE benefits ADD PRIMARY KEY (job_id, type)"))
        conn.commit()
    print("Primary keys added.")

    # ------------------------------------------------------------------
    # Recreate analytics view
    # ------------------------------------------------------------------
    with engine.connect() as conn:
        conn.execute(text("DROP VIEW IF EXISTS analytics"))
        conn.execute(text("""
            CREATE VIEW analytics AS
            SELECT
                p.job_id,
                p.title,
                p.location,
                p.formatted_work_type        AS work_type,
                p.formatted_experience_level AS experience_level,
                p.remote_allowed,
                c.name                       AS company_name,
                c.company_size,
                c.country,
                i.industry_name,
                sk.skill_name,
                s.min_salary,
                s.max_salary,
                s.med_salary,
                s.pay_period,
                s.normalized_yearly
            FROM postings p
            LEFT JOIN companies      c  ON p.company_id   = c.company_id
            LEFT JOIN salaries       s  ON p.job_id       = s.job_id
            LEFT JOIN job_industries ji ON p.job_id       = ji.job_id
            LEFT JOIN industries     i  ON ji.industry_id = i.industry_id
            LEFT JOIN job_skills     js ON p.job_id       = js.job_id
            LEFT JOIN skills         sk ON js.skill_abr   = sk.skill_abr
        """))
        conn.commit()
    print("Analytics view created.")

    print(f"\nDone. Data loaded into MySQL database '{DB_CONFIG['database']}' on {DB_CONFIG['host']}")


if __name__ == "__main__":
    run_etl()
