import pytest
from grimoire.models import SessionLocal, Book, UserRating

def test_db_counts():
    db = SessionLocal()
    users_count = db.query(UserRating.username).distinct().count()
    books_count = db.query(Book).count()
    print(f"Users in DB: {users_count}")
    print(f"Books in DB: {books_count}")
    db.close()
