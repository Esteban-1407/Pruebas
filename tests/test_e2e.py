import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from database import Base



# Base de datos de prueba (SQLite en memoria)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_library.db")

# Detectar si es SQLite y usar connect_args solo en ese caso
if TEST_DATABASE_URL.startswith("sqlite"):
    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    test_engine = create_engine(TEST_DATABASE_URL)

# Crear sesión para pruebas
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """Cliente de prueba con base de datos limpia"""
    Base.metadata.create_all(bind=test_engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=test_engine)


def test_get_authors_returns_200_and_complete_list(client):
    """Prueba 1: GET /authors retorna lista completa y código 200"""
    # Crear algunos autores primero
    author1_data = {"name": "Gabriel García Márquez", "nationality": "Colombian"}
    author2_data = {"name": "Isabel Allende", "nationality": "Chilean"}

    client.post("/authors", json=author1_data)
    client.post("/authors", json=author2_data)

    # Probar GET /authors
    response = client.get("/authors")

    assert response.status_code == 200
    authors = response.json()
    assert len(authors) == 2

    # Verificar que los datos fueron transformados correctamente
    assert authors[0]["name"] == "Gabriel García Márquez"
    assert authors[0]["nationality"] == "Colombian"
    assert authors[1]["name"] == "Isabel Allende"
    assert authors[1]["nationality"] == "Chilean"

    # Verificar que cada autor tiene un ID
    assert "id" in authors[0]
    assert "id" in authors[1]
    assert isinstance(authors[0]["id"], int)
    assert isinstance(authors[1]["id"], int)


def test_post_books_creates_element_and_returns_201(client):
    """Prueba 2: POST /books crea elemento y retorna 201 con datos"""
    # Primero crear un autor
    author_data = {"name": "mario vargas llosa", "nationality": "peruvian"}
    author_response = client.post("/authors", json=author_data)
    author_id = author_response.json()["id"]

    # Crear un libro
    book_data = {
        "title": "la ciudad y los perros",
        "isbn": "9780374529963",
        "author_id": author_id
    }

    response = client.post("/books", json=book_data)

    assert response.status_code == 201
    created_book = response.json()

    # Verificar respuesta (datos transformados)
    assert created_book["title"] == "LA CIUDAD Y LOS PERROS"  # Mayúsculas
    assert created_book["isbn"] == "ISBN-9780374529963"  # Prefijo agregado
    assert created_book["author_id"] == author_id
    assert created_book["available"] == True  # Por defecto disponible
    assert "id" in created_book
    assert isinstance(created_book["id"], int)

    # Verificar que el libro fue realmente creado consultándolo
    get_response = client.get(f"/books/{created_book['id']}")
    assert get_response.status_code == 200
    retrieved_book = get_response.json()
    assert retrieved_book["title"] == "LA CIUDAD Y LOS PERROS"
    assert retrieved_book["isbn"] == "ISBN-9780374529963"


def test_delete_loans_removes_and_returns_204_then_get_returns_404(client):
    """Prueba 3: DELETE /loans/:id elimina y retorna 204, luego GET retorna 404"""
    # Configurar datos de prueba
    # 1. Crear autor
    author_data = {"name": "Julio Cortázar", "nationality": "Argentinian"}
    author_response = client.post("/authors", json=author_data)
    author_id = author_response.json()["id"]

    # 2. Crear libro
    book_data = {
        "title": "Rayuela",
        "isbn": "9780394752846",
        "author_id": author_id
    }
    book_response = client.post("/books", json=book_data)
    book_id = book_response.json()["id"]

    # 3. Crear préstamo
    loan_data = {
        "book_id": book_id,
        "user_name": "María González"
    }
    create_loan_response = client.post("/loans", json=loan_data)
    assert create_loan_response.status_code == 201

    loan_id = create_loan_response.json()["id"]

    # Verificar que el préstamo existe antes de eliminarlo
    get_loan_response = client.get(f"/loans/{loan_id}")
    assert get_loan_response.status_code == 200
    loan_data_retrieved = get_loan_response.json()
    assert loan_data_retrieved["user_name"] == "María González"
    assert loan_data_retrieved["returned"] == False

    # Verificar que el libro no está disponible
    book_check = client.get(f"/books/{book_id}")
    assert book_check.json()["available"] == False

    # Eliminar el préstamo
    delete_response = client.delete(f"/loans/{loan_id}")
    assert delete_response.status_code == 204

    # Verificar que el préstamo no existe más
    get_after_delete = client.get(f"/loans/{loan_id}")
    assert get_after_delete.status_code == 404
    assert get_after_delete.json()["detail"] == "Loan not found"

    # Verificar que el libro vuelve a estar disponible
    book_check_after = client.get(f"/books/{book_id}")
    assert book_check_after.json()["available"] == True

    # Verificar que no está en la lista de préstamos
    all_loans_response = client.get("/loans")
    assert all_loans_response.status_code == 200
    loans_list = all_loans_response.json()
    loan_ids = [loan["id"] for loan in loans_list]
    assert loan_id not in loan_ids