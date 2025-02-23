from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from enum import Enum as PyEnum

class ReservationStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)
    reserved_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    book = relationship("Book", back_populates="reservations")
    user = relationship("User", back_populates="reservations", foreign_keys=[user_id])
    librarian = relationship("User", foreign_keys=[approved_by], overlaps="reservations_approved")

