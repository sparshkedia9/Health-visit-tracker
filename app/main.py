from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models  # noqa: F401  (imported so the tables are registered)
from app.database import Base, engine
from app.routers import dashboard, households, reports, visits
from app.templating import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates any missing tables when the server starts.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Health Worker Visit Tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

app.include_router(dashboard.router)
app.include_router(households.router)
app.include_router(visits.router)
app.include_router(reports.router)


@app.exception_handler(StarletteHTTPException)
async def show_error_page(request: Request, exc: StarletteHTTPException):
    """Show a friendly HTML page instead of raw JSON for 404s and similar errors."""
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exc.status_code, "message": exc.detail},
        status_code=exc.status_code,
    )
