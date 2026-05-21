import pytest
import numpy as np
from grimoire import jobs
from grimoire.models import Book, UserRating, Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_matrix(db_session):
    db_session.add(Book(id="1", title="The Same Book", num_votes=100))
    db_session.add(Book(id="2", title="the same book", num_votes=200))
    db_session.add(UserRating(username="u1", book_id="1", rating=5.0))
    db_session.commit()
    
    matrix = jobs.get_normalized_matrix(db_session)
    assert "1" in matrix.columns
    assert "2" not in matrix.columns

def test_calculate_recommendations(db_session):
    db_session.add(User(username="target"))
    db_session.add(User(username="user1"))
    db_session.add(User(username="user2"))
    
    db_session.add(Book(id="b1", title="Book 1", num_votes=50))
    db_session.add(Book(id="b2", title="Book 2", num_votes=50))
    db_session.add(Book(id="b3", title="Book 3", num_votes=50))
    
    db_session.add(UserRating(username="target", book_id="b1", rating=5.0))
    db_session.add(UserRating(username="user1", book_id="b1", rating=5.0))
    db_session.add(UserRating(username="user1", book_id="b2", rating=4.0))
    db_session.add(UserRating(username="user2", book_id="b1", rating=1.0))
    db_session.add(UserRating(username="user2", book_id="b3", rating=5.0))
    db_session.commit()

    top_books, top_users = jobs.calculate_recommendations(db_session, "target")
    
    book_ids = [b[0] for b in top_books]
    assert "b2" in book_ids
    assert "b1" not in book_ids
    assert len(top_users) > 0


