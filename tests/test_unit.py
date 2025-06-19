import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from main import validate_author_data, transform_book_data, calculate_loan_statistics
from models import AuthorCreate, BookCreate




class MockLoan:
    def __init__(self, returned: bool):
        self.returned = returned


def test_validate_author_data():
    """Prueba 1: Validación de datos de autor"""
    # Datos válidos
    valid_author = AuthorCreate(name="Gabriel García Márquez", nationality="Colombian")
    assert validate_author_data(valid_author) == True

    # Datos inválidos - nombre vacío
    invalid_author1 = AuthorCreate(name="", nationality="Colombian")
    assert validate_author_data(invalid_author1) == False

    # Datos inválidos - nacionalidad vacía
    invalid_author2 = AuthorCreate(name="Gabriel García Márquez", nationality="")
    assert validate_author_data(invalid_author2) == False

    # Datos inválidos - solo espacios
    invalid_author3 = AuthorCreate(name="   ", nationality="   ")
    assert validate_author_data(invalid_author3) == False


def test_transform_book_data():
    """Prueba 2: Transformación de datos de libro"""
    book = BookCreate(title="cien años de soledad", isbn="9780060883287", author_id=1)
    result = transform_book_data(book)

    # El título debe estar en mayúsculas
    assert result["title"] == "CIEN AÑOS DE SOLEDAD"

    # El ISBN debe tener prefijo
    assert result["isbn"] == "ISBN-9780060883287"

    # El author_id debe mantenerse
    assert result["author_id"] == 1

    # Probar con espacios
    book_with_spaces = BookCreate(
        title="  el amor en los tiempos del cólera  ",
        isbn="  9780307389732  ",
        author_id=2
    )
    result2 = transform_book_data(book_with_spaces)

    assert result2["title"] == "EL AMOR EN LOS TIEMPOS DEL CÓLERA"
    assert result2["isbn"] == "ISBN-9780307389732"


def test_calculate_loan_statistics():
    """Prueba 3: Función utilitaria de estadísticas de préstamos"""
    # Lista vacía
    empty_loans = []
    stats_empty = calculate_loan_statistics(empty_loans)
    assert stats_empty == {"total": 0, "returned": 0, "pending": 0}

    # Lista con préstamos mixtos
    loans = [
        MockLoan(returned=True),  # Devuelto
        MockLoan(returned=False),  # Pendiente
        MockLoan(returned=True),  # Devuelto
        MockLoan(returned=False),  # Pendiente
        MockLoan(returned=False)  # Pendiente
    ]

    stats = calculate_loan_statistics(loans)
    assert stats["total"] == 5
    assert stats["returned"] == 2
    assert stats["pending"] == 3

    # Solo préstamos devueltos
    all_returned = [MockLoan(returned=True), MockLoan(returned=True)]
    stats_all_returned = calculate_loan_statistics(all_returned)
    assert stats_all_returned == {"total": 2, "returned": 2, "pending": 0}

    # Solo préstamos pendientes
    all_pending = [MockLoan(returned=False), MockLoan(returned=False)]
    stats_all_pending = calculate_loan_statistics(all_pending)
    assert stats_all_pending == {"total": 2, "returned": 0, "pending": 2}