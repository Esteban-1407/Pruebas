import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Author, Book, Loan
from datetime import datetime
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Base de datos de prueba (SQLite en memoria)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_library.db")
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine)


@pytest.fixture
def db_session():
    """Sesión de prueba para base de datos"""
    Base.metadata.create_all(bind=test_engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_insert_author_to_database(db_session):
    """Prueba 1: Insertar autor en base de datos"""
    # Crear un nuevo autor
    author = Author(
        name="Isabel Allende",
        nationality="Chilean"
    )

    # Insertar en base de datos
    db_session.add(author)
    db_session.commit()
    db_session.refresh(author)

    # Verificar inserción
    assert author.id is not None
    assert author.name == "Isabel Allende"
    assert author.nationality == "Chilean"

    # Verificar que existe en la base de datos
    db_author = db_session.query(Author).filter(Author.id == author.id).first()
    assert db_author is not None
    assert db_author.name == "Isabel Allende"
    assert db_author.nationality == "Chilean"


def test_query_books_from_database(db_session):
    """Prueba 2: Consultar libros de base de datos"""
    # Insertar datos de prueba
    author = Author(name="Julio Cortázar", nationality="Argentinian")
    db_session.add(author)
    db_session.commit()

    book1 = Book(
        title="Rayuela",
        isbn="ISBN-9780394752846",
        author_id=author.id,
        available=True
    )
    book2 = Book(
        title="Casa Tomada",
        isbn="ISBN-9780394752847",
        author_id=author.id,
        available=False
    )

    db_session.add_all([book1, book2])
    db_session.commit()

    # Consultar todos los libros
    books = db_session.query(Book).all()
    assert len(books) == 2

    # Consultar libro específico por título
    found_book = db_session.query(Book).filter(Book.title == "Rayuela").first()
    assert found_book is not None
    assert found_book.isbn == "ISBN-9780394752846"
    assert found_book.available == True

    # Consultar libros disponibles
    available_books = db_session.query(Book).filter(Book.available == True).all()
    assert len(available_books) == 1
    assert available_books[0].title == "Rayuela"

    # Consultar por ID del autor
    author_books = db_session.query(Book).filter(Book.author_id == author.id).all()
    assert len(author_books) == 2


def test_delete_loan_from_database(db_session):
    """Prueba 3: Eliminar préstamo de base de datos"""
    # Insertar datos de prueba
    author = Author(name="Mario Vargas Llosa", nationality="Peruvian")
    db_session.add(author)
    db_session.commit()

    book = Book(
        title="La Ciudad y los Perros",
        isbn="ISBN-9780374529963",
        author_id=author.id,
        available=False
    )
    db_session.add(book)
    db_session.commit()

    loan = Loan(
        book_id=book.id,
        user_name="Juan Pérez",
        loan_date=datetime.utcnow(),
        returned=False
    )
    db_session.add(loan)
    db_session.commit()
    loan_id = loan.id

    # Verificar que el préstamo existe
    existing_loan = db_session.query(Loan).filter(Loan.id == loan_id).first()
    assert existing_loan is not None
    assert existing_loan.user_name == "Juan Pérez"
    assert existing_loan.returned == False

    # Eliminar el préstamo
    db_session.delete(existing_loan)
    db_session.commit()

    # Verificar que el préstamo fue eliminado
    deleted_loan = db_session.query(Loan).filter(Loan.id == loan_id).first()
    assert deleted_loan is None

    # Verificar que el libro y autor aún existen
    remaining_book = db_session.query(Book).filter(Book.id == book.id).first()
    remaining_author = db_session.query(Author).filter(Author.id == author.id).first()
    assert remaining_book is not None
    assert remaining_author is not None

    # Verificar conteo de préstamos
    remaining_loans = db_session.query(Loan).all()
    assert len(remaining_loans) == 0