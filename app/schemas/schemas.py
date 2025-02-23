from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum

# 🟢 Ролі користувачів
class UserRole(str, Enum):
    librarian = "librarian"
    reader = "reader"

# 🟢 Базові схеми користувачів
class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr

class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=100)]
    secret_code: Optional[str] = None  # Код для бібліотекаря (необов’язковий)

class UserResponse(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True  # ✅ Виправлено

# 🔹 Авторизація та токени
class Token(BaseModel):
    access_token: str
    token_type: str

# 🔹 Схеми для відновлення пароля
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: Annotated[str, Field(min_length=8, max_length=100)]

# 📚 Схеми книг
class BookBase(BaseModel):
    title: str
    author: str
    year: int
    category: str
    language: str
    description: str
    cover_image: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None

    class Config:
        from_attributes = True  # ✅ Виправлено

class BookResponse(BookBase):
    id: int
    is_available: bool = True  # ✅ Додано дефолтне значення

    class Config:
        from_attributes = True  # ✅ Виправлено

# 📌 Бронювання книг
class ReservationBase(BaseModel):
    book_id: int

class ReservationResponse(BaseModel):
    id: int
    book_id: int
    user_id: int
    status: str
    reserved_at: datetime
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True  # ✅ Виправлено

# ⭐ Відгуки на книги
class ReviewBase(BaseModel):
    book_id: int
    rating: Annotated[int, Field(ge=1, le=5)]  # ✅ Обмежено оцінку від 1 до 5
    comment: str

class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # ✅ Виправлено
