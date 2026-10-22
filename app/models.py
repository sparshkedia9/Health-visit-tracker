from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VISIT_STATUSES = ["scheduled", "completed", "missed"]
FOLLOW_UP_STATUSES = ["pending", "completed"]

# Tasks a health worker can tick off during a visit.
CHECKLIST_ITEMS = [
    "Checked vital signs",
    "Reviewed vaccination records",
    "Reviewed medication",
    "Checked maternal / child health",
    "Checked water and sanitation",
    "Gave health education",
    "Made a referral",
]


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    contact_number: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Deleting a household also deletes all of its visits.
    visits: Mapped[list["Visit"]] = relationship(
        back_populates="household",
        cascade="all, delete-orphan",
        order_by="Visit.scheduled_at.desc()",
    )


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # List of completed checklist item names, e.g. ["Checked vital signs"].
    checklist: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    follow_up_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    household: Mapped[Household] = relationship(back_populates="visits")

    @property
    def follow_up_state(self) -> str | None:
        """'pending', 'overdue' or 'completed' — or None if no follow-up is set.

        'overdue' isn't stored in the database; it's worked out from today's date.
        """
        if self.follow_up_date is None:
            return None
        if self.follow_up_status == "completed":
            return "completed"
        if self.follow_up_date < date.today():
            return "overdue"
        return "pending"
