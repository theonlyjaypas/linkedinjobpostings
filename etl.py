"""
ETL script — LinkedIn Job Postings (2023-2024)
Loads and cleans all 11 CSV files into linkedin_jobs.db (SQLite)
"""

import sqlite3
import pandas as pd
import os

DB_PATH = "linkedin_jobs.db"

# Multipliers to convert any pay period to annual salary
PERIOD_TO_YEARLY = {
    "HOURLY":    2080,   # 40 hrs/wk * 52 weeks
    "WEEKLY":    52,
    "BIWEEKLY":  26,
    "MONTHLY":   12,
    "YEARLY":    1,
}


def normalize_yearly(row):
    """Convert min/max/med salary to annual based on pay_period."""
    multiplier = PERIOD_TO_YEARLY.get(str(row.get("pay_period", "")).upper(), None)
    if multiplier is None:
        return None
    # Prefer max_salary, fall back to med, then min
    val = row.get("max_salary") or row.get("med_salary") or row.get("min_salary")
    if pd.isna(val) or val is None:
        return None
    return round(float(val) * multiplier, 2)


def load_csv(path):
    return pd.read_csv(path, low_memory=False)


def run_etl():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")   # off during bulk load

    with open("schema.sql") as f:
        conn.executescript(f.read())
    print("Schema created.")

    # ------------------------------------------------------------------
    # 1. industries
    # ------------------------------------------------------------------
    df = load_csv("mappings/industries.csv")
    df = df.dropna(subset=["industry_name"])
    df = df.rename(columns={"industry_id": "industry_id", "industry_name": "industry_name"})
    df.to_sql("industries", conn, if_exists="append", index=False)
    print(f"industries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 2. skills
    # ------------------------------------------------------------------
    df = load_csv("mappings/skills.csv")
    df = df.dropna(subset=["skill_name"])
    df.to_sql("skills", conn, if_exists="append", index=False)
    print(f"skills: {len(df)} rows")

    # ------------------------------------------------------------------
    # 3. companies
    # ------------------------------------------------------------------
    df = load_csv("companies/companies.csv")
    df = df.rename(columns={"name": "name"})
    df = df[["company_id", "name", "company_size", "state", "country", "city", "url"]]
    df = df.dropna(subset=["company_id"])
    df["company_id"] = df["company_id"].astype(int)
    df.to_sql("companies", conn, if_exists="append", index=False)
    print(f"companies: {len(df)} rows")

    # ------------------------------------------------------------------
    # 4. company_industries
    # ------------------------------------------------------------------
    df = load_csv("companies/company_industries.csv")
    # Map industry name -> industry_id via the industries table
    ind_map = pd.read_sql("SELECT industry_id, industry_name FROM industries", conn)
    ind_name_to_id = dict(zip(ind_map["industry_name"], ind_map["industry_id"]))
    df["industry_id"] = df["industry"].map(ind_name_to_id)
    df = df.dropna(subset=["company_id", "industry_id"])
    df["company_id"] = df["company_id"].astype(int)
    df["industry_id"] = df["industry_id"].astype(int)
    df = df[["company_id", "industry_id"]].drop_duplicates()
    df.to_sql("company_industries", conn, if_exists="append", index=False)
    print(f"company_industries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 5. employee_counts — keep latest snapshot per company
    # ------------------------------------------------------------------
    df = load_csv("companies/employee_counts.csv")
    df = df.dropna(subset=["company_id"])
    df["company_id"] = df["company_id"].astype(int)
    df = df.sort_values("time_recorded", ascending=False).drop_duplicates(subset=["company_id"])
    df = df[["company_id", "employee_count", "follower_count", "time_recorded"]]
    df.to_sql("employee_counts", conn, if_exists="append", index=False)
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
    df.to_sql("postings", conn, if_exists="append", index=False)
    print(f"postings: {len(df)} rows")

    # ------------------------------------------------------------------
    # 7. salaries
    # ------------------------------------------------------------------
    df = load_csv("jobs/salaries.csv")
    df = df.dropna(subset=["job_id"])
    df["job_id"] = df["job_id"].astype(int)
    df["normalized_yearly"] = df.apply(normalize_yearly, axis=1)
    df = df.rename(columns={
        "max_salary": "max_salary",
        "med_salary": "med_salary",
        "min_salary": "min_salary",
    })
    df = df[["salary_id", "job_id", "min_salary", "med_salary", "max_salary",
             "pay_period", "currency", "compensation_type", "normalized_yearly"]]
    df.to_sql("salaries", conn, if_exists="append", index=False)
    print(f"salaries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 8. job_skills
    # ------------------------------------------------------------------
    df = load_csv("jobs/job_skills.csv")
    df = df.dropna(subset=["job_id", "skill_abr"])
    df["job_id"] = df["job_id"].astype(int)
    # Keep only skills that exist in the skills table
    valid_skills = set(pd.read_sql("SELECT skill_abr FROM skills", conn)["skill_abr"])
    df = df[df["skill_abr"].isin(valid_skills)]
    df = df.drop_duplicates()
    df.to_sql("job_skills", conn, if_exists="append", index=False)
    print(f"job_skills: {len(df)} rows")

    # ------------------------------------------------------------------
    # 9. job_industries
    # ------------------------------------------------------------------
    df = load_csv("jobs/job_industries.csv")
    df = df.dropna(subset=["job_id", "industry_id"])
    df["job_id"] = df["job_id"].astype(int)
    df["industry_id"] = df["industry_id"].astype(int)
    # Keep only valid industry_ids
    valid_ind = set(pd.read_sql("SELECT industry_id FROM industries", conn)["industry_id"])
    df = df[df["industry_id"].isin(valid_ind)]
    df = df.drop_duplicates()
    df.to_sql("job_industries", conn, if_exists="append", index=False)
    print(f"job_industries: {len(df)} rows")

    # ------------------------------------------------------------------
    # 10. benefits
    # ------------------------------------------------------------------
    df = load_csv("jobs/benefits.csv")
    df = df.dropna(subset=["job_id", "type"])
    df["job_id"] = df["job_id"].astype(int)
    df["inferred"] = df["inferred"].fillna(0).astype(int)
    df = df.drop_duplicates(subset=["job_id", "type"])
    df.to_sql("benefits", conn, if_exists="append", index=False)
    print(f"benefits: {len(df)} rows")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    size_mb = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"\nDone. Database saved to {DB_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    run_etl()
