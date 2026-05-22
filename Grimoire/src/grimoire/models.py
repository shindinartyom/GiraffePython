from sqlalchemy import create_engine, Column, Integer, String, Float, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./grimoire.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 15})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configures SQLite connection pragmas for concurrent access.

    Enables Write-Ahead Logging (WAL) and sets synchronous mode to NORMAL
    to allow concurrent reads and writes without locking errors.

    Args:
        dbapi_connection: The raw SQLite database API connection object.
        connection_record: The connection record object from SQLAlchemy.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    
class Book(Base):
    __tablename__ = "books"
    id = Column(String, primary_key=True)
    title = Column(String, index=True)
    authors = Column(String)
    categories = Column(String)
    description = Column(String)
    average_rating = Column(Float)
    page_count = Column(Integer)
    num_votes = Column(Integer, default=0)
    cover_url = Column(String)
    slug = Column(String)

class UserRating(Base):
    __tablename__ = "user_ratings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, index=True)
    book_id = Column(String)
    rating = Column(Float)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, index=True)
    book_id = Column(String)
    score = Column(Float)

class UserSimilarity(Base):
    __tablename__ = "user_similarities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_username = Column(String, index=True)
    similar_username = Column(String)
    similarity_score = Column(Float)

def init_db():
    """Creates all tables in the database."""
    Base.metadata.create_all(bind=engine)

def reset_db():
    """Deletes and recreates all tables in the database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
