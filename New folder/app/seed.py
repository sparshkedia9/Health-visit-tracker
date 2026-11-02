"""Adds sample households and visits to the database, for demos and testing.

Run from the project folder:
    python -m app.seed

Safe to run more than once: a household whose name already exists is skipped
(along with its visits), so nothing is duplicated.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import CHECKLIST_ITEMS, Household, Visit

# ---------- Sample data (edit or add to these lists) ----------

HOUSEHOLDS = [
    {
        "name": "Mehta family",
        "contact_number": "+91 98200 11111",
        "address": "14 Station Road, Shivaji Nagar",
        "location": "Ward 2, near water tank",
    },
    {
        "name": "Fernandes family",
        "contact_number": "+91 98200 22222",
        "address": "House 7, Church Lane",
        "location": "Ward 3, opposite St. Mary's church",
    },
    {
        "name": "Iyer family",
        "contact_number": "+91 98200 33333",
        "address": "22 Temple Street",
        "location": "Ward 1, behind the market",
    },
    {
        "name": "Singh family",
        "contact_number": "+91 98200 44444",
        "address": "Plot 5, Green Park Colony",
        "location": "Ward 4, near primary school",
    },
    {
        "name": "Banerjee family",
        "contact_number": "+91 98200 55555",
        "address": "3 Lake View Road",
        "location": "Ward 2, next to the post office",
    },
]

# Each visit says which household it belongs to (by name) and when it happens.
# "day" is relative to today: -3 means 3 days ago, 0 is today, 2 is in 2 days.
# "follow_up" is optional: (day relative to today, "pending" or "completed").
VISITS = [
    {
        "household": "Mehta family",
        "day": -10, "time": "10:00",
        "status": "completed",
        "checklist": ["Checked vital signs", "Reviewed medication"],
        "notes": "Grandfather's blood pressure slightly high (150/95).\nAdvised less salt and regular medication.",
        "follow_up": (-3, "pending"),  # date has passed -> shows as overdue
    },
    {
        "household": "Mehta family",
        "day": 0, "time": "11:00",
        "status": "scheduled",
        "notes": "Follow-up blood pressure check.",
    },
    {
        "household": "Fernandes family",
        "day": -7, "time": "09:30",
        "status": "completed",
        "checklist": ["Reviewed vaccination records", "Checked maternal / child health", "Gave health education"],
        "notes": "Baby (6 months) due for next vaccination dose.",
        "follow_up": (5, "pending"),
    },
    {
        "household": "Fernandes family",
        "day": 5, "time": "10:00",
        "status": "scheduled",
        "notes": "Vaccination follow-up.",
    },
    {
        "household": "Iyer family",
        "day": -5, "time": "14:00",
        "status": "missed",
        "notes": "Nobody at home. Neighbour said family is travelling.",
    },
    {
        "household": "Iyer family",
        "day": -2, "time": "15:00",
        "status": "scheduled",  # in the past but not yet marked completed or missed
    },
    {
        "household": "Singh family",
        "day": -14, "time": "11:30",
        "status": "completed",
        "checklist": ["Checked water and sanitation", "Gave health education", "Made a referral"],
        "notes": "Child with recurring diarrhoea. Referred to the health centre.\nAdvised boiling drinking water.",
        "follow_up": (-7, "completed"),
    },
    {
        "household": "Singh family",
        "day": 2, "time": "12:00",
        "status": "scheduled",
    },
    {
        "household": "Banerjee family",
        "day": 0, "time": "15:30",
        "status": "scheduled",
        "notes": "First visit: registration and general check-up.",
    },
    {
        "household": "Banerjee family",
        "day": 9, "time": "10:30",
        "status": "scheduled",
    },
]


# ---------- Code that inserts the data ----------

def make_visit(data: dict) -> Visit:
    """Turns one entry from VISITS into a Visit object."""
    visit_day = date.today() + timedelta(days=data["day"])
    hour, minute = map(int, data["time"].split(":"))
    scheduled_at = datetime(visit_day.year, visit_day.month, visit_day.day, hour, minute)

    checklist = data.get("checklist", [])
    for item in checklist:
        if item not in CHECKLIST_ITEMS:
            raise ValueError(f"Unknown checklist item: {item!r}. It must match CHECKLIST_ITEMS in models.py.")

    visit = Visit(
        scheduled_at=scheduled_at,
        status=data["status"],
        checklist=checklist,
        notes=data.get("notes", ""),
    )
    if data["status"] == "completed":
        visit.completed_at = scheduled_at + timedelta(hours=1)
    if "follow_up" in data:
        follow_up_day, follow_up_status = data["follow_up"]
        visit.follow_up_date = date.today() + timedelta(days=follow_up_day)
        visit.follow_up_status = follow_up_status
    return visit


def seed() -> None:
    Base.metadata.create_all(bind=engine)  # in case the server hasn't created the tables yet
    db = SessionLocal()
    try:
        added = 0
        for household_data in HOUSEHOLDS:
            name = household_data["name"]
            if db.scalar(select(Household).where(Household.name == name)):
                print(f"Skipped {name} (already exists)")
                continue

            household = Household(**household_data)
            # Adding visits to household.visits links them through the relationship,
            # so SQLAlchemy fills in household_id for us.
            household.visits = [make_visit(v) for v in VISITS if v["household"] == name]
            db.add(household)
            added += 1
            print(f"Added {name} with {len(household.visits)} visits")

        db.commit()
        print(f"Done. {added} household(s) added.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
