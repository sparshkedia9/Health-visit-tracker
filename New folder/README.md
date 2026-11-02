# Health Worker Visit Tracker

A web application that helps community health workers manage household visits, schedule appointments, record visit details, and track follow-up activities.

Built as a college project using **FastAPI**, **PostgreSQL**, **SQLAlchemy** and server-rendered **Jinja2** HTML templates.

---

## Problem Statement

Community health workers record scheduled visits and follow-up activities across many households. Managing these records manually makes it hard to organise visits and keep track of pending follow-ups.

## Objective

Provide a simple, field-friendly system to plan and record community health visits, manage household information, and monitor follow-up activities.

---

## Features

**Dashboard**
- Total households, today's visits, completed visits, missed visits and pending follow-ups
- Lists of today's visits, upcoming visits and pending follow-ups

**Household management**
- Add, view, edit and delete households (name, contact number, address, location)
- Search households by name, address or location
- Each household has a details page listing all of its visits

**Visit management**
- Schedule a visit for an existing household with a date and time
- Visit status: **scheduled**, **completed** or **missed**
- Checklist of tasks done during the visit (vital signs, vaccinations, medication, etc.)
- Notes about observations and advice given
- Follow-up date with status **pending**, **completed** or **overdue**
- One-click "Mark follow-up done" and "Schedule follow-up visit"

**Reports**
- Filter visits by date range, household and visit status
- Summary counts and completion rate
- Export the filtered visits as a CSV file

**Validation and errors**
- Form input is validated (e.g. phone number format, follow-up date can't be before the visit date); errors are shown next to the field
- Friendly error page for missing records (e.g. 404 "Household not found")

**Responsive design**
- One shared CSS file; layouts stack on phones and use two columns on laptops

---

## Tech Stack

| Technology | Role |
|---|---|
| Python + FastAPI | Web framework: maps URLs to Python functions |
| Uvicorn | Server that runs the FastAPI app |
| PostgreSQL | Database that stores households and visits |
| SQLAlchemy | ORM: work with database tables as Python classes |
| psycopg | Driver SQLAlchemy uses to connect to PostgreSQL |
| Pydantic | Validates data submitted through forms |
| Jinja2 | Renders HTML templates with data |
| HTML + CSS | User interface |
| python-dotenv | Loads database credentials from a `.env` file |

---

## Project Structure

```
html_project/
├── app/
│   ├── main.py            # Creates the app, registers routers, error page handler
│   ├── database.py        # Database connection and session (reads DATABASE_URL)
│   ├── models.py          # Household and Visit tables (SQLAlchemy models)
│   ├── schemas.py         # Form validation rules (Pydantic)
│   ├── templating.py      # Jinja2 setup and date formatting filters
│   ├── routers/           # One module per section of the site
│   │   ├── dashboard.py
│   │   ├── households.py
│   │   ├── visits.py
│   │   └── reports.py
│   ├── templates/         # HTML pages (Jinja2)
│   │   ├── base.html      # Shared layout and navigation
│   │   ├── macros.html    # Reusable pieces: badges, errors, visit table
│   │   ├── dashboard.html
│   │   ├── reports.html
│   │   ├── error.html
│   │   ├── households/    # list, form, detail
│   │   └── visits/        # list, form, detail
│   └── static/            # CSS file
├── .env.example           # Template for database settings
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Database Design

**households**

| Column | Type | Notes |
|---|---|---|
| id | integer | Primary key |
| name | varchar(120) | Household name |
| contact_number | varchar(20) | |
| address | varchar(255) | |
| location | varchar(120) | Village / ward / landmark or GPS coordinates |
| created_at | timestamp | Set automatically |

**visits**

| Column | Type | Notes |
|---|---|---|
| id | integer | Primary key |
| household_id | integer | Foreign key → households.id |
| scheduled_at | timestamp | Visit date and time |
| status | varchar(20) | scheduled / completed / missed |
| checklist | JSON | List of completed checklist items |
| notes | text | |
| follow_up_date | date | Optional |
| follow_up_status | varchar(20) | pending / completed (empty if no follow-up) |
| completed_at | timestamp | Set when the visit is marked completed |

**Relationship:** one household has many visits (one-to-many). Deleting a household also deletes its visits.

---

## Setup Instructions (Windows)

**1. Requirements:** Python 3.11+ and PostgreSQL installed.

**2. Create and activate a virtual environment**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**3. Install dependencies**
```powershell
pip install -r requirements.txt
```

**4. Create the database**

In pgAdmin: right-click **Databases → Create → Database**, and name it `visit_tracker`.

**5. Configure the connection**

Copy `.env.example` to `.env` and put in your PostgreSQL password:
```
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/visit_tracker
```
Special characters in the password must be URL-encoded (e.g. `@` → `%40`).

**6. Run the server**
```powershell
uvicorn app.main:app --reload
```
The tables are created automatically on first start. Open **http://127.0.0.1:8000** in a browser.

---

## Main Pages

| URL | Page |
|---|---|
| `/` | Dashboard |
| `/households` | Household list and search |
| `/households/new` | Add a household |
| `/households/{id}` | Household details and its visits |
| `/visits` | All visits, filterable by status |
| `/visits/new` | Schedule a visit |
| `/visits/{id}` | Visit details, checklist, notes, follow-up |
| `/reports` | Filtered summaries |
| `/reports/export.csv` | CSV download of filtered visits |

---

## Design Decisions

- **Server-rendered HTML.** Pages are built on the server with Jinja2, so no JavaScript framework is needed and pages stay light on slow connections.
- **"Overdue" is calculated, not stored.** A follow-up is overdue when it's still pending and its date has passed. Calculating this each time means it is always correct, with no scheduled job needed to update it.
- **Validation with friendly errors.** Forms are validated with Pydantic inside the route, so invalid input re-displays the form with messages instead of returning a raw error.
- **Redirect after saving (Post/Redirect/Get).** After a form is saved the browser is redirected with HTTP 303, so refreshing the page doesn't submit the form twice.
- **Credentials in environment variables.** The database password lives in `.env`, which is excluded from version control.
- **Small route modules.** Each section (dashboard, households, visits, reports) has its own router file.

---

## Future Enhancements

- Offline draft saving, so form data isn't lost when the internet drops
- Sample data script for demonstrations
- Database migrations with Alembic
- User login for health workers
