# from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
# from sqlalchemy.orm import relationship
# from app.database import Base

# class Review(Base):
#     __tablename__ = "reviews"

#     id = Column(Integer, primary_key=True, index=True)
#     book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     rating = Column(Integer, nullable=False)
#     comment = Column(String, nullable=False)
#     created_at = Column(DateTime, server_default=func.now(), nullable=False)

#     # 🔹 Визначаємо зв’язки між таблицями
#     book = relationship("app.models.book.Book", back_populates="reviews")
#     user = relationship("app.models.user.User", back_populates="reviews")
