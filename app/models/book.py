from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    language = Column(String, nullable=False)
    description = Column(String, nullable=False)
    cover_image = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    reservations = relationship(
        "Reservation",
        back_populates="book",
        cascade="all, delete-orphan"
    )

    reviews = relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan"
    )

