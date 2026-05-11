# LinkedIn Job Postings - Analytics Dashboard

An interactive analytics dashboard built with Streamlit that explores ~124,000 LinkedIn job postings collected between 2023 and 2024. The app surfaces trends in hiring demand, salary expectations, in-demand skills, and industry breakdowns across 388 industries and 24,000+ companies.

**DATA 201 · Group 2**


## Features

**Six dashboard pages:**

| Page | What it shows |
|------|---------------|
| Overview | KPI cards, top skills & industries, remote vs. on-site salary, salary by experience level |
| Skills | Most in-demand skills, highest paying skills, salary-vs-demand bubble chart |
| Industries | Hiring volume by industry, average salary by industry, best industry + skill combinations |
| Companies | Top companies by hiring volume and by average salary |
| Salary Insights | Salary breakdown by experience level, work type, remote/on-site, and job title |
| Job Search | Full-text search by keyword, skill, and industry with dynamic salary distribution charts |

## Tech Stack

- **Frontend / App** — [Streamlit](https://streamlit.io/) + CSS
- **Charts** — [Plotly Express](https://plotly.com/python/plotly-express/)
- **Database** — MySQL
- **ORM / Query** — SQLAlchemy + pandas
- **ETL** — pandas + mysql-connector-python



## Project Structure

```
.
├── app.py            # DASHBOARD USING STREAMLIT
├── analyze_data.py   # ANALYTICS PIPELINE USING MYSQL
├── load_data.py      # ETL PIPELINE
├── schema.sql        # DATABASE SCHEMA
└── data/             # DATASET (NOT COMMITTED)
    ├── postings.csv
    ├── mappings/
    │   ├── industries.csv
    │   └── skills.csv
    ├── companies/
    │   ├── companies.csv
    │   ├── company_industries.csv
    │   └── employee_counts.csv
    └── jobs/
        ├── salaries.csv
        ├── job_skills.csv
        ├── job_industries.csv
        └── benefits.csv
```



## Database Schema

```
industries        skills
     │                │
     ├─ company_industries    job_skills ─┘
     │                              │
companies ──── postings ────── job_industries
     │              │
employee_counts  salaries
                     │
                  benefits
```

An `analytics` view denormalizes the core tables for fast dashboard queries.



## Setup

### 1. Install dependencies

```bash
pip install streamlit plotly pandas sqlalchemy mysql-connector-python
```

### 2. Configure the database connection

Set environment variables (or edit `DB_CONFIG` in `load_data.py` / `analyze_data.py`):

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=linkedin_jobs
```

### 3. Create the database

```bash
mysql -u root -p -e "CREATE DATABASE linkedin_jobs;"
```

### 4. Load the data

Place all source CSVs in the layout shown above, then run the ETL:

```bash
python load_data.py
```

This drops and recreates all tables, loads the 11 CSVs with cleaning and normalization applied, adds primary keys, and rebuilds the `analytics` view.

### 5. Run the dashboard

```bash
streamlit run app.py
```



## Analytics Queries

`analyze_data.py` has 12 functions, each returning a pandas DataFrame:

| Function | Description |
|----------|-------------|
| `top_skills_by_demand(limit)` | Skills ranked by number of job postings |
| `top_skills_by_salary(limit)` | Skills ranked by average annual salary |
| `top_industries_by_hiring(limit)` | Industries ranked by hiring volume |
| `top_industries_by_salary(limit)` | Industries ranked by average annual salary |
| `top_companies_by_hiring(limit)` | Companies ranked by job postings |
| `top_companies_by_salary(limit)` | Companies ranked by average annual salary |
| `salary_by_experience()` | Min/avg/max salary per experience level |
| `salary_by_work_type()` | Average salary by work type (full-time, contract, etc.) |
| `top_job_titles_by_salary(limit)` | Job titles ranked by average annual salary |
| `best_industry_skill_combos(limit)` | Industry + skill pairs ranked by salary |
| `remote_vs_onsite_salary()` | Remote vs. on-site salary comparison |
| `search_jobs(keyword, skill, industry, limit)` | Filtered job search |

Salaries are normalized to annual USD across all pay periods (hourly, weekly, biweekly, monthly, yearly).


## About the Dataset

The dataset is a collection of job postings on LinkedIn between 2023 and 2024, consisting of close to 124,000 postings from a wide range of companies and industries, it is HISTORIC. Each posting includes:

- Job titles and roles
- Company names
- Industry categories
- Salary information (median and maximum pay)
- Required skills
- Job benefits

The data is split across 11 CSV files, each focusing on a different aspect of the postings — industries, skills, benefits, salaries, and more. The breadth of the dataset across multiple industries and companies makes it well-suited for meaningful analytics on job demand and salary expectations.

**Source:** [LinkedIn Job Postings (Kaggle)](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings)

- ~123,849 postings
- 24,473 companies
- 388 industries
- 35 tracked skills

**NOTE**: Since the dataset is huge, we were not able to include the file on Github. Since the DB file is attached, the streamlit app will work regardless. But, if you want to test the ETL pipeline, download the dataset from Kaggle and saved it under the `data/` directory.
