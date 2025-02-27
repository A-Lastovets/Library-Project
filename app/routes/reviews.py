# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from app.database import get_db
# from app.models.review import Review
# from app.models.user import User
# from app.models.book import Book
# from app.schemas.schemas import ReviewBase, ReviewResponse
# from app.services.user_service import get_current_user

# router = APIRouter(tags=["reviews"])

# @router.post("/reviews", response_model=ReviewResponse)
# async def create_review(
#     review: ReviewBase, 
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "reader":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

#     db_book = await db.get(Book, review.book_id)
#     if not db_book:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

#     # 📌 Перевіряємо, чи користувач вже залишав відгук на цю книгу
#     existing_review = await db.execute(
#         select(Review).where(Review.book_id == review.book_id, Review.user_id == current_user.id)
#     )
#     if existing_review.scalar_one_or_none():
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review already exists for this book")

#     db_review = Review(**review.model_dump(), user_id=current_user.id)
#     db.add(db_review)
#     await db.commit()
#     await db.refresh(db_review)

#     return db_review
