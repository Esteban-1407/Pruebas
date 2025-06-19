from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import engine, get_db, Base
from models import (
    Author, Book, Loan,
    AuthorCreate, AuthorResponse,
    BookCreate, BookResponse,
    LoanCreate, LoanResponse
)

# Crear las tablas
Base.metadata.create_all(bind=engine)

# Crear la app
app = FastAPI(title="Biblioteca Digital API", version="1.0.0")


# ===========================================
# FUNCIONES PARA PRUEBAS UNITARIAS
# ===========================================

def validate_author_data(author: AuthorCreate) -> bool:
    """Validar datos del autor - nombre y nacionalidad no vacíos"""
    return bool(author.name.strip() and author.nationality.strip())


def transform_book_data(book: BookCreate) -> dict:
    """Transformar datos del libro - título en mayúsculas y ISBN formateado"""
    return {
        "title": book.title.strip().upper(),
        "isbn": f"ISBN-{book.isbn.strip()}",
        "author_id": book.author_id
    }


def calculate_loan_statistics(loans: List[Loan]) -> dict:
    """Función utilitaria - calcular estadísticas de préstamos"""
    if not loans:
        return {"total": 0, "returned": 0, "pending": 0}

    total = len(loans)
    returned = sum(1 for loan in loans if loan.returned)
    pending = total - returned

    return {
        "total": total,
        "returned": returned,
        "pending": pending
    }


# ===========================================
# ENDPOINTS DE LA API
# ===========================================

@app.get("/")
def root():
    return {"message": "Biblioteca Digital API funcionando!"}


# --- AUTHOR ENDPOINTS ---
@app.get("/authors", response_model=List[AuthorResponse])
def get_authors(db: Session = Depends(get_db)):
    """Obtener todos los autores"""
    authors = db.query(Author).all()
    return authors


@app.get("/authors/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    """Obtener autor por ID"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.post("/authors", response_model=AuthorResponse, status_code=201)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    """Crear nuevo autor"""
    # Validar
    if not validate_author_data(author):
        raise HTTPException(status_code=400, detail="Name and nationality cannot be empty")

    # Crear
    db_author = Author(
        name=author.name.strip().title(),
        nationality=author.nationality.strip().title()
    )
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


@app.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    """Eliminar autor"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    db.delete(author)
    db.commit()
    return None


# --- BOOK ENDPOINTS ---
@app.get("/books", response_model=List[BookResponse])
def get_books(db: Session = Depends(get_db)):
    """Obtener todos los libros"""
    books = db.query(Book).all()
    return books


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Obtener libro por ID"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    """Crear nuevo libro"""
    # Verificar que el autor existe
    author = db.query(Author).filter(Author.id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=400, detail="Author not found")

    # Transformar datos
    transformed_data = transform_book_data(book)

    # Crear
    db_book = Book(**transformed_data)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Eliminar libro"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()
    return None


# --- LOAN ENDPOINTS ---
@app.get("/loans", response_model=List[LoanResponse])
def get_loans(db: Session = Depends(get_db)):
    """Obtener todos los préstamos"""
    loans = db.query(Loan).all()
    return loans


@app.get("/loans/{loan_id}", response_model=LoanResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    """Obtener préstamo por ID"""
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@app.post("/loans", response_model=LoanResponse, status_code=201)
def create_loan(loan: LoanCreate, db: Session = Depends(get_db)):
    """Crear nuevo préstamo"""
    # Verificar que el libro existe y está disponible
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=400, detail="Book not found")
    if not book.available:
        raise HTTPException(status_code=400, detail="Book not available")

    # Crear préstamo
    db_loan = Loan(
        book_id=loan.book_id,
        user_name=loan.user_name.strip().title()
    )

    # Marcar libro como no disponible
    book.available = False

    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


@app.delete("/loans/{loan_id}", status_code=204)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    """Eliminar/devolver préstamo"""
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    # Marcar libro como disponible nuevamente
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if book:
        book.available = True

    db.delete(loan)
    db.commit()
    return None


# --- ENDPOINTS ADICIONALES ---
@app.get("/books/{book_id}/availability")
def check_book_availability(book_id: int, db: Session = Depends(get_db)):
    """Verificar disponibilidad de un libro"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return {"book_id": book_id, "available": book.available}


@app.get("/statistics")
def get_loan_statistics(db: Session = Depends(get_db)):
    """Obtener estadísticas de préstamos"""
    loans = db.query(Loan).all()
    stats = calculate_loan_statistics(loans)
    return stats