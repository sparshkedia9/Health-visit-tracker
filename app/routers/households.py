from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Household, Visit
from app.schemas import HouseholdForm, errors_by_field
from app.templating import templates

router = APIRouter(prefix="/households")

FORM_FIELDS = ("name", "contact_number", "address", "location")


def get_household_or_404(db: Session, household_id: int) -> Household:
    household = db.get(Household, household_id)
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found.")
    return household


async def read_form(request: Request) -> dict:
    form = await request.form()
    return {field: form.get(field, "") for field in FORM_FIELDS}


def render_form(request: Request, form: dict, errors: dict, household: Household | None = None):
    return templates.TemplateResponse(
        request,
        "households/form.html",
        {"active": "households", "form": form, "errors": errors, "household": household},
        status_code=400 if errors else 200,
    )


@router.get("")
def list_households(request: Request, q: str = "", db: Session = Depends(get_db)):
    visit_count = (
        select(func.count(Visit.id)).where(Visit.household_id == Household.id).scalar_subquery()
    )
    query = select(Household, visit_count).order_by(Household.name)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            or_(Household.name.ilike(term), Household.address.ilike(term), Household.location.ilike(term))
        )
    rows = db.execute(query).all()
    return templates.TemplateResponse(
        request, "households/list.html", {"active": "households", "rows": rows, "q": q}
    )


@router.get("/new")
def new_household_form(request: Request):
    return render_form(request, form={field: "" for field in FORM_FIELDS}, errors={})


@router.post("/new")
async def create_household(request: Request, db: Session = Depends(get_db)):
    form = await read_form(request)
    try:
        data = HouseholdForm(**form)
    except ValidationError as exc:
        return render_form(request, form, errors_by_field(exc))

    household = Household(**data.model_dump())
    db.add(household)
    db.commit()
    # 303 tells the browser to follow up with a GET, so refreshing won't resubmit the form.
    return RedirectResponse(f"/households/{household.id}", status_code=303)


@router.get("/{household_id}")
def show_household(request: Request, household_id: int, db: Session = Depends(get_db)):
    household = get_household_or_404(db, household_id)
    return templates.TemplateResponse(
        request, "households/detail.html", {"active": "households", "household": household}
    )


@router.get("/{household_id}/edit")
def edit_household_form(request: Request, household_id: int, db: Session = Depends(get_db)):
    household = get_household_or_404(db, household_id)
    form = {field: getattr(household, field) for field in FORM_FIELDS}
    return render_form(request, form, errors={}, household=household)


@router.post("/{household_id}/edit")
async def update_household(request: Request, household_id: int, db: Session = Depends(get_db)):
    household = get_household_or_404(db, household_id)
    form = await read_form(request)
    try:
        data = HouseholdForm(**form)
    except ValidationError as exc:
        return render_form(request, form, errors_by_field(exc), household=household)

    for field, value in data.model_dump().items():
        setattr(household, field, value)
    db.commit()
    return RedirectResponse(f"/households/{household.id}", status_code=303)


@router.post("/{household_id}/delete")
def delete_household(household_id: int, db: Session = Depends(get_db)):
    household = get_household_or_404(db, household_id)
    db.delete(household)
    db.commit()
    return RedirectResponse("/households", status_code=303)
