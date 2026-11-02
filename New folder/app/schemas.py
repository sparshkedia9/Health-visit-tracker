"""Pydantic models that validate data submitted through the HTML forms."""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.models import CHECKLIST_ITEMS

PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 \-]{6,18}$")


class HouseholdForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    contact_number: str
    address: str = Field(min_length=3, max_length=255)
    location: str = Field(default="", max_length=120)

    @field_validator("contact_number")
    @classmethod
    def check_phone(cls, value: str) -> str:
        if not PHONE_PATTERN.match(value):
            raise ValueError("Enter a valid phone number (digits, spaces, dashes, optional +).")
        return value


class VisitForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    household_id: int
    scheduled_at: datetime
    status: Literal["scheduled", "completed", "missed"] = "scheduled"
    checklist: list[str] = []
    notes: str = Field(default="", max_length=5000)
    follow_up_date: date | None = None
    follow_up_status: Literal["pending", "completed"] | None = None

    @field_validator("household_id", mode="before")
    @classmethod
    def require_household(cls, value):
        if value in ("", None):
            raise ValueError("Please choose a household.")
        return value

    @field_validator("scheduled_at", mode="before")
    @classmethod
    def require_schedule(cls, value):
        if value in ("", None):
            raise ValueError("Please enter the visit date and time.")
        return value

    # HTML forms send "" for empty fields; treat that as "not set".
    @field_validator("follow_up_date", "follow_up_status", mode="before")
    @classmethod
    def empty_to_none(cls, value):
        return None if value == "" else value

    @field_validator("checklist")
    @classmethod
    def known_items_only(cls, items: list[str]) -> list[str]:
        return [item for item in items if item in CHECKLIST_ITEMS]

    @model_validator(mode="after")
    def check_follow_up(self):
        if self.follow_up_date is None:
            self.follow_up_status = None
            return self
        if self.follow_up_date < self.scheduled_at.date():
            raise ValueError("follow_up_date: Follow-up date can't be before the visit date.")
        if self.follow_up_status is None:
            self.follow_up_status = "pending"
        return self


def errors_by_field(exc: ValidationError) -> dict[str, str]:
    """Turn a Pydantic ValidationError into {field_name: message} for the templates."""
    errors = {}
    for error in exc.errors():
        message = error["msg"].removeprefix("Value error, ")
        field = str(error["loc"][0]) if error["loc"] else ""
        # Errors from the model-level validator are written as "field: message".
        if not field and ": " in message:
            field, message = message.split(": ", 1)
        errors.setdefault(field or "form", message)
    return errors
