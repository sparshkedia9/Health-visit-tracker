import csv
import io
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import VISIT_STATUSES, Household, Visit
from app.templating import templates

router = APIRouter(prefix="/reports")


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def filtered_visits(db: Session, date_from: str, date_to: str, household_id: str, status: str) -> list[Visit]:
    """Visits matching the report filters. Empty or invalid filters are ignored."""
    query = select(Visit).options(joinedload(Visit.household)).order_by(Visit.scheduled_at)

    start = parse_date(date_from)
    if start:
        query = query.where(Visit.scheduled_at >= datetime.combine(start, time.min))
    end = parse_date(date_to)
    if end:
        # "To" date is inclusive, so compare against the start of the next day.
        query = query.where(Visit.scheduled_at < datetime.combine(end + timedelta(days=1), time.min))
    if household_id.isdigit():
        query = query.where(Visit.household_id == int(household_id))
    if status in VISIT_STATUSES:
        query = query.where(Visit.status == status)

    return list(db.scalars(query).all())


def summarize(visits: list[Visit]) -> dict:
    total = len(visits)
    completed = sum(v.status == "completed" for v in visits)
    follow_up_states = [v.follow_up_state for v in visits]
    return {
        "total": total,
        "completed": completed,
        "scheduled": sum(v.status == "scheduled" for v in visits),
        "missed": sum(v.status == "missed" for v in visits),
        "completion_rate": round(completed / total * 100) if total else 0,
        "follow_ups_pending": follow_up_states.count("pending"),
        "follow_ups_overdue": follow_up_states.count("overdue"),
        "follow_ups_completed": follow_up_states.count("completed"),
    }


@router.get("")
def show_reports(
    request: Request,
    date_from: str = "",
    date_to: str = "",
    household_id: str = "",
    status: str = "",
    db: Session = Depends(get_db),
):
    visits = filtered_visits(db, date_from, date_to, household_id, status)
    households = db.scalars(select(Household).order_by(Household.name)).all()
    return templates.TemplateResponse(
        request,
        "reports.html",
        {
            "active": "reports",
            "visits": visits,
            "summary": summarize(visits),
            "households": households,
            "visit_statuses": VISIT_STATUSES,
            "filters": {"date_from": date_from, "date_to": date_to, "household_id": household_id, "status": status},
        },
    )


@router.get("/export.csv")
def export_csv(
    date_from: str = "",
    date_to: str = "",
    household_id: str = "",
    status: str = "",
    db: Session = Depends(get_db),
):
    visits = filtered_visits(db, date_from, date_to, household_id, status)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Visit ID", "Household", "Contact", "Location", "Scheduled", "Status",
         "Checklist done", "Notes", "Follow-up date", "Follow-up status", "Completed at"]
    )
    for v in visits:
        writer.writerow([
            v.id,
            v.household.name,
            v.household.contact_number,
            v.household.location,
            v.scheduled_at.strftime("%Y-%m-%d %H:%M"),
            v.status,
            "; ".join(v.checklist or []),
            v.notes,
            v.follow_up_date.isoformat() if v.follow_up_date else "",
            v.follow_up_state or "",
            v.completed_at.strftime("%Y-%m-%d %H:%M") if v.completed_at else "",
        ])

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=visit_report.csv"},
    )
