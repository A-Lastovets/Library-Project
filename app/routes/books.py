from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.database import get_db
from app.models.book import Book
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.schemas import BookCreate, BookResponse, BookUpdate
from app.services.user_service import get_current_user

router = APIRouter(tags=["books"])

# 🟢 Додавання книги (тільки бібліотекар)
@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    db_book = Book(**book.model_dump())
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book

# 🟡 Отримати всі книги (з фільтрами)
@router.get("/books", response_model=list[BookResponse], status_code=status.HTTP_200_OK)
async def read_books(
    author: str | None = Query(None),
    title: str | None = Query(None),
    category: str | None = Query(None),
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Book)
    
    if author:
        query = query.where(Book.author.ilike(f"%{author}%"))
    if title:
        query = query.where(Book.title.ilike(f"%{title}%"))
    if category:
        query = query.where(Book.category.ilike(f"%{category}%"))

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

# 🟡 Отримати одну книгу за ID
@router.get("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def read_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

# 🔵 Оновлення книги (тільки бібліотекар)
@router.put("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def update_book(
    book_id: int, 
    book_update: BookUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalar_one_or_none()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)
    await db.execute(update(Book).where(Book.id == book_id).values(**update_data))
    await db.commit()

    result = await db.execute(select(Book).where(Book.id == book_id))
    updated_book = result.scalar_one_or_none()
    return updated_book

# 🔴 Видалення книги (тільки бібліотекар)
@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "librarian":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # ❗Перевіряємо, чи книга в бронюванні
    reservation_check = await db.execute(select(Reservation).where(Reservation.book_id == book_id))
    if reservation_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a book that is reserved.")

    await db.execute(delete(Book).where(Book.id == book_id))
    await db.commit()
