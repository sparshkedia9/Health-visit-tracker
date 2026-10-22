from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import CHECKLIST_ITEMS, VISIT_STATUSES, Household, Visit
from app.schemas import VisitForm, errors_by_field
from app.templating import templates

router = APIRouter(prefix="/visits")

DATETIME_INPUT_FORMAT = "%Y-%m-%dT%H:%M"  # what <input type="datetime-local"> expects


def get_visit_or_404(db: Session, visit_id: int) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return visit


async def read_form(request: Request) -> dict:
    form = await request.form()
    data = {
        field: form.get(field, "")
        for field in ("household_id", "scheduled_at", "status", "notes", "follow_up_date", "follow_up_status")
    }
    # Checkboxes with the same name arrive as several values, so use getlist().
    data["checklist"] = form.getlist("checklist")
    return data


def visit_to_form(visit: Visit) -> dict:
    return {
        "household_id": str(visit.household_id),
        "scheduled_at": visit.scheduled_at.strftime(DATETIME_INPUT_FORMAT),
        "status": visit.status,
        "notes": visit.notes,
        "follow_up_date": visit.follow_up_date.isoformat() if visit.follow_up_date else "",
        "follow_up_status": visit.follow_up_status or "",
        "checklist": visit.checklist or [],
    }


def render_form(request: Request, db: Session, form: dict, errors: dict, visit: Visit | None = None):
    households = db.scalars(select(Household).order_by(Household.name)).all()
    return templates.TemplateResponse(
        request,
        "visits/form.html",
        {
            "active": "visits",
            "form": form,
            "errors": errors,
            "visit": visit,
            "households": households,
            "checklist_items": CHECKLIST_ITEMS,
            "visit_statuses": VISIT_STATUSES,
        },
        status_code=400 if errors else 200,
    )


def validate(db: Session, form: dict) -> tuple[VisitForm | None, dict]:
    """Returns (valid data, {}) or (None, errors)."""
    try:
        data = VisitForm(**form)
    except ValidationError as exc:
        return None, errors_by_field(exc)
    if db.get(Household, data.household_id) is None:
        return None, {"household_id": "That household no longer exists."}
    return data, {}


def apply_form(visit: Visit, data: VisitForm) -> None:
    for field, value in data.model_dump().items():
        setattr(visit, field, value)
    # Record when the visit was first marked completed; clear it if un-completed.
    if visit.status == "completed":
        visit.completed_at = visit.completed_at or datetime.now()
    else:
        visit.completed_at = None


@router.get("")
def list_visits(request: Request, status: str = "", db: Session = Depends(get_db)):
    query = select(Visit).options(joinedload(Visit.household)).order_by(Visit.scheduled_at.desc())
    if status in VISIT_STATUSES:
        query = query.where(Visit.status == status)
    visits = db.scalars(query).all()
    return templates.TemplateResponse(
        request,
        "visits/list.html",
        {"active": "visits", "visits": visits, "status": status, "visit_statuses": VISIT_STATUSES},
    )


@router.get("/new")
def new_visit_form(request: Request, household_id: str = "", date: str = "", db: Session = Depends(get_db)):
    # household_id and date can be pre-filled from links, e.g. "Schedule follow-up visit".
    form = {
        "household_id": household_id,
        "scheduled_at": f"{date}T09:00" if date else "",
        "status": "scheduled",
        "notes": "",
        "follow_up_date": "",
        "follow_up_status": "",
        "checklist": [],
    }
    return render_form(request, db, form, errors={})


@router.post("/new")
async def create_visit(request: Request, db: Session = Depends(get_db)):
    form = await read_form(request)
    data, errors = validate(db, form)
    if errors:
        return render_form(request, db, form, errors)

    visit = Visit()
    apply_form(visit, data)
    db.add(visit)
    db.commit()
    return RedirectResponse(f"/visits/{visit.id}", status_code=303)


@router.get("/{visit_id}")
def show_visit(request: Request, visit_id: int, db: Session = Depends(get_db)):
    visit = get_visit_or_404(db, visit_id)
    return templates.TemplateResponse(
        request,
        "visits/detail.html",
        {"active": "visits", "visit": visit, "checklist_items": CHECKLIST_ITEMS},
    )


@router.get("/{visit_id}/edit")
def edit_visit_form(request: Request, visit_id: int, db: Session = Depends(get_db)):
    visit = get_visit_or_404(db, visit_id)
    return render_form(request, db, visit_to_form(visit), errors={}, visit=visit)


@router.post("/{visit_id}/edit")
async def update_visit(request: Request, visit_id: int, db: Session = Depends(get_db)):
    visit = get_visit_or_404(db, visit_id)
    form = await read_form(request)
    data, errors = validate(db, form)
    if errors:
        return render_form(request, db, form, errors, visit=visit)

    apply_form(visit, data)
    db.commit()
    return RedirectResponse(f"/visits/{visit.id}", status_code=303)


@router.post("/{visit_id}/follow-up-done")
def complete_follow_up(visit_id: int, db: Session = Depends(get_db)):
    visit = get_visit_or_404(db, visit_id)
    if visit.follow_up_date is not None:
        visit.follow_up_status = "completed"
        db.commit()
    return RedirectResponse(f"/visits/{visit.id}", status_code=303)


@router.post("/{visit_id}/delete")
def delete_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = get_visit_or_404(db, visit_id)
    household_id = visit.household_id
    db.delete(visit)
    db.commit()
    return RedirectResponse(f"/households/{household_id}", status_code=303)
