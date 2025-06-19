from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime
from database import Base


# ===========================================
# MODELOS DE BASE DE DATOS (SQLAlchemy)
# ===========================================

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nationality = Column(String, nullable=False)

    # Relación con libros
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    isbn = Column(String, nullable=False, unique=True)
    author_id = Column(Integer, ForeignKey("authors.id"))
    available = Column(Boolean, default=True)

    # Relaciones
    author = relationship("Author", back_populates="books")
    loans = relationship("Loan", back_populates="book")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_name = Column(String, nullable=False)
    loan_date = Column(DateTime, default=datetime.utcnow)
    returned = Column(Boolean, default=False)

    # Relación
    book = relationship("Book", back_populates="loans")


# ===========================================
# MODELOS PYDANTIC PARA LA API
# ===========================================

# --- AUTHOR MODELS ---
class AuthorCreate(BaseModel):
    name: str
    nationality: str


class AuthorResponse(BaseModel):
    id: int
    name: str
    nationality: str

    class Config:
        from_attributes = True


# --- BOOK MODELS ---
class BookCreate(BaseModel):
    title: str
    isbn: str
    author_id: int


class BookResponse(BaseModel):
    id: int
    title: str
    isbn: str
    author_id: int
    available: bool

    class Config:
        from_attributes = True


# --- LOAN MODELS ---
class LoanCreate(BaseModel):
    book_id: int
    user_name: str


class LoanResponse(BaseModel):
    id: int
    book_id: int
    user_name: str
    loan_date: datetime
    returned: bool

    class Config:
        from_attributes = True