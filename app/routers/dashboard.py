from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Household, Visit
from app.templating import templates

router = APIRouter()


def count(db: Session, *conditions) -> int:
    return db.scalar(select(func.count(Visit.id)).where(*conditions))


@router.get("/")
def show_dashboard(request: Request, db: Session = Depends(get_db)):
    start_of_today = datetime.combine(date.today(), time.min)
    start_of_tomorrow = start_of_today + timedelta(days=1)
    is_today = (Visit.scheduled_at >= start_of_today, Visit.scheduled_at < start_of_tomorrow)

    stats = {
        "households": db.scalar(select(func.count(Household.id))),
        "today": count(db, *is_today),
        "completed": count(db, Visit.status == "completed"),
        "missed": count(db, Visit.status == "missed"),
        "pending_follow_ups": count(db, Visit.follow_up_status == "pending"),
    }

    todays_visits = db.scalars(
        select(Visit).options(joinedload(Visit.household)).where(*is_today).order_by(Visit.scheduled_at)
    ).all()

    upcoming_visits = db.scalars(
        select(Visit)
        .options(joinedload(Visit.household))
        .where(Visit.status == "scheduled", Visit.scheduled_at >= start_of_tomorrow)
        .order_by(Visit.scheduled_at)
        .limit(10)
    ).all()

    follow_ups = db.scalars(
        select(Visit)
        .options(joinedload(Visit.household))
        .where(Visit.follow_up_status == "pending")
        .order_by(Visit.follow_up_date)
        .limit(10)
    ).all()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active": "dashboard",
            "stats": stats,
            "todays_visits": todays_visits,
            "upcoming_visits": upcoming_visits,
            "follow_ups": follow_ups,
        },
    )
