from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def day_name(value: date) -> str:
    """'Today', 'Tomorrow' or 'Yesterday' when close to today, otherwise e.g. '22 Oct 2026'."""
    today = date.today()
    if value == today:
        return "Today"
    if value == today + timedelta(days=1):
        return "Tomorrow"
    if value == today - timedelta(days=1):
        return "Yesterday"
    return value.strftime("%d %b %Y")


def format_datetime(value: datetime | None) -> str:
    return f"{day_name(value.date())}, {value.strftime('%I:%M %p')}" if value else "—"


def format_date(value: date | None) -> str:
    return day_name(value) if value else "—"


templates.env.filters["datetime"] = format_datetime
templates.env.filters["date"] = format_date
