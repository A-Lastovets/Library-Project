from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum

# ✅ Базова схема для автоматичної конвертації в camelCase
class BaseSchema(BaseModel):
    class Config:
        alias_generator = lambda string: ''.join(
            word.capitalize() if i else word for i, word in enumerate(string.split('_'))
        )  # ✅ Конвертує snake_case → camelCase
        populate_by_name = True  # ✅ Дозволяє приймати snake_case, але повертати camelCase

class UserRole(str, Enum):
    librarian = "librarian"
    reader = "reader"

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = "user@example.com"
    password: Optional[str] = "password"

class UserBase(BaseSchema):
    firstName: Annotated[str, Field(min_length=3, max_length=50)]
    lastName: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr

class UserCreate(BaseSchema):
    firstName: str = Field(..., min_length=3, max_length=50)
    lastName: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    confirmPassword: str = Field(..., min_length=8, max_length=100)
    secretCode: Optional[str] = None

    @field_validator("confirmPassword")
    @classmethod
    def passwords_match(cls, confirmPassword: str, values):
        """Перевіряємо, чи `password` і `confirmPassword` співпадають."""
        if values.data.get("password") and confirmPassword != values.data["password"]:
            raise ValueError("Passwords do not match")
        return confirmPassword

class UserResponse(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseSchema):
    accessToken: str = Field(..., alias="accessToken") 
    tokenType: str = Field(..., alias="tokenType")
    user: UserResponse

class PasswordResetRequest(BaseSchema):
    email: EmailStr

class PasswordReset(BaseSchema):
    token: str
    newPassword: Annotated[str, Field(min_length=8, max_length=100)]

# class BookBase(BaseSchema):
#     title: str
#     author: str
#     year: int
#     category: str
#     language: str
#     description: str
#     coverImage: Optional[str] = Field(None, alias="cover_image")

# class BookCreate(BookBase):
#     pass

# class BookUpdate(BaseSchema):
#     title: Optional[str] = None
#     author: Optional[str] = None
#     year: Optional[int] = None
#     category: Optional[str] = None
#     language: Optional[str] = None
#     description: Optional[str] = None
#     coverImage: Optional[str] = Field(None, alias="cover_image")

#     class Config:
#         from_attributes = True

# class BookResponse(BookBase):
#     id: int
#     isAvailable: bool = Field(True, alias="is_available")

#     class Config:
#         from_attributes = True 

# class ReservationBase(BaseSchema):
#     bookId: int = Field(..., alias="book_id")

# class ReservationResponse(BaseSchema):
#     id: int
#     bookId: int = Field(..., alias="book_id") 
#     userId: int = Field(..., alias="user_id")
#     status: str
#     reservedAt: datetime = Field(..., alias="reserved_at")
#     dueDate: Optional[datetime] = Field(None, alias="due_date")

#     class Config:
#         from_attributes = True

# class ReviewBase(BaseSchema):
#     bookId: int = Field(..., alias="book_id")
#     rating: Annotated[int, Field(ge=1, le=5)]
#     comment: str

# class ReviewResponse(ReviewBase):
#     id: int
#     userId: int = Field(..., alias="user_id")
#     createdAt: datetime = Field(..., alias="created_at")

#     class Config:
#         from_attributes = True
