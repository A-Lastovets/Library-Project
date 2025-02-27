from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum as PyEnum

class RoleEnum(PyEnum):
    reader = "reader"
    librarian = "librarian"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String, index=True, nullable=False)
    lastName = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashedPassword = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.reader, nullable=False)

    # reservations = relationship(
    #     "Reservation",
    #     back_populates="user",
    #     foreign_keys="[Reservation.userId]"
    # )
    
    # reservationsApproved = relationship(
    #     "Reservation",
    #     foreign_keys="[Reservation.approvedBy]"
    # )

    # reviews = relationship("Review", back_populates="user")
