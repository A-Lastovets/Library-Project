from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta

from app.database import get_db
from app.models.reservation import Reservation, ReservationStatus
from app.models.book import Book
from app.models.user import User
from app.schemas.schemas import ReservationBase, ReservationResponse
from app.services.user_service import get_current_user
from app.services.email_tasks import send_reservation_email

router = APIRouter(tags=["reservations"])

@router.post("/reservations", response_model=ReservationResponse)
async def create_reservation(
    reservation: ReservationBase, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "reader":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    db_book = await db.get(Book, reservation.book_id)
    if not db_book or not db_book.is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book not available")

    db_reservation = Reservation(
        book_id=reservation.book_id,
        user_id=current_user.id,
        status=ReservationStatus.PENDING
    )

    # 📌 Робимо книгу недоступною після бронювання
    db_book.is_available = False

    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation)

    return db_reservation

# 📌 Підтвердити бронювання (бібліотекар)
@router.put("/reservations/{reservation_id}/approve", response_model=ReservationResponse)
async def approve_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    if reservation.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation is not pending")

    due_date = datetime.now() + timedelta(days=14)
    await db.execute(update(Reservation).where(Reservation.id == reservation_id).values(
        status=ReservationStatus.APPROVED,
        due_date=due_date,
        approved_by=current_user.id
    ))
    await db.commit()

    # 📩 Перевіряємо чи є email перед надсиланням повідомлення
    if not reservation.user or not reservation.user.email:
        raise HTTPException(status_code=500, detail="User email not found for reservation")

    send_reservation_email.delay(reservation.user.email, reservation.book.title, due_date.strftime("%Y-%m-%d"))

    return reservation

# 📌 Відхилити бронювання (бібліотекар)
@router.put("/reservations/{reservation_id}/reject", response_model=ReservationResponse)
async def reject_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    if reservation.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation is not pending")

    await db.execute(update(Reservation).where(Reservation.id == reservation_id).values(
        status=ReservationStatus.REJECTED
    ))
    await db.commit()

    return reservation

# 📌 Позначити книгу як повернуту (бібліотекар)
@router.put("/reservations/{reservation_id}/return", response_model=ReservationResponse)
async def return_book(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    if reservation.status != ReservationStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is not currently borrowed")

    # 📌 Оновлюємо статус книги
    await db.execute(update(Reservation).where(Reservation.id == reservation_id).values(
        status=ReservationStatus.RETURNED
    ))

    # 📌 Робимо книгу доступною знову після повернення
    db_book = await db.get(Book, reservation.book_id)
    if db_book:
        db_book.is_available = True

    await db.commit()

    return reservation
