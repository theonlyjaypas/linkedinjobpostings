-- ============================================================
-- DATA 201 Group 2 -- LinkedIn Job Postings Database Schema
-- ============================================================

-- ---- Lookup / Dimension Tables ----

CREATE TABLE IF NOT EXISTS industries (
    industry_id   INTEGER PRIMARY KEY,
    industry_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    skill_abr  TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL
);

-- ---- Company Tables ----

CREATE TABLE IF NOT EXISTS companies (
    company_id   INTEGER PRIMARY KEY,
    name         TEXT,
    company_size INTEGER,   -- LinkedIn size bucket (1-7)
    state        TEXT,
    country      TEXT,
    city         TEXT,
    url          TEXT
);

CREATE TABLE IF NOT EXISTS company_industries (
    company_id  INTEGER REFERENCES companies(company_id),
    industry_id INTEGER REFERENCES industries(industry_id),
    PRIMARY KEY (company_id, industry_id)
);

CREATE TABLE IF NOT EXISTS employee_counts (
    company_id     INTEGER PRIMARY KEY REFERENCES companies(company_id),
    employee_count INTEGER,
    follower_count INTEGER,
    time_recorded  INTEGER
);

-- ---- Job / Posting Tables ----

CREATE TABLE IF NOT EXISTS postings (
    job_id                     INTEGER PRIMARY KEY,
    company_id                 INTEGER REFERENCES companies(company_id),
    title                      TEXT,
    location                   TEXT,
    formatted_work_type        TEXT,
    formatted_experience_level TEXT,
    remote_allowed             INTEGER DEFAULT 0,  -- 0/1 boolean
    listed_time                INTEGER            -- Unix timestamp
);

CREATE TABLE IF NOT EXISTS salaries (
    salary_id             INTEGER PRIMARY KEY,
    job_id                INTEGER REFERENCES postings(job_id),
    min_salary            REAL,
    med_salary            REAL,
    max_salary            REAL,
    pay_period            TEXT,
    currency              TEXT,
    compensation_type     TEXT,
    normalized_yearly     REAL    -- all converted to annual USD
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id    INTEGER REFERENCES postings(job_id),
    skill_abr TEXT    REFERENCES skills(skill_abr),
    PRIMARY KEY (job_id, skill_abr)
);

CREATE TABLE IF NOT EXISTS job_industries (
    job_id      INTEGER REFERENCES postings(job_id),
    industry_id INTEGER REFERENCES industries(industry_id),
    PRIMARY KEY (job_id, industry_id)
);

CREATE TABLE IF NOT EXISTS benefits (
    job_id   INTEGER REFERENCES postings(job_id),
    type     TEXT,
    inferred INTEGER DEFAULT 0,
    PRIMARY KEY (job_id, type)
);

-- ============================================================
-- Analytical View — denormalized for fast dashboard queries
-- ============================================================

CREATE VIEW IF NOT EXISTS analytics AS
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
LEFT JOIN companies     c  ON p.company_id  = c.company_id
LEFT JOIN salaries      s  ON p.job_id      = s.job_id
LEFT JOIN job_industries ji ON p.job_id     = ji.job_id
LEFT JOIN industries    i  ON ji.industry_id = i.industry_id
LEFT JOIN job_skills    js ON p.job_id      = js.job_id
LEFT JOIN skills        sk ON js.skill_abr  = sk.skill_abr;
