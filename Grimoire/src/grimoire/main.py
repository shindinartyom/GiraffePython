from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from grimoire.models import SessionLocal, init_db, Book, Recommendation, UserRating, User, UserSimilarity
from grimoire import jobs
from grimoire import books_api
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown lifecycle of the application.

    Args:
        app (fastapi.FastAPI): The FastAPI application instance.
    """
    scheduler = BackgroundScheduler()
    jobs.get_known_users()
    scheduler.add_job(jobs.fetch_new_users, 'interval', minutes=5, next_run_time=datetime.now() + timedelta(seconds=5))
    scheduler.add_job(jobs.continuous_sync, 'interval', seconds=2)
    scheduler.add_job(jobs.recalculate_all_recommendations, 'interval', minutes=60, next_run_time=datetime.now() + timedelta(seconds=10))
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Grimoire", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

def get_db():
    """Yields a database session.

    Yields:
        sqlalchemy.orm.Session: A database session to be used in endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/recommend/{username}")
def get_recommendations(username: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Retrieves book recommendations and similar users for a given Hardcover username.

    If the user exists in the local database, it instantly serves cached recommendations.
    If the user does not exist, it fetches their profile from the Hardcover API, ingests
    their ratings, and generates fresh recommendations dynamically.

    Args:
        username (str): The Hardcover username to fetch recommendations for.
        background_tasks (fastapi.BackgroundTasks): FastAPI background task manager.
        db (sqlalchemy.orm.Session): The database session.

    Returns:
        dict: A JSON response containing personalized recommendations and similar users, 
              or a 404 response if the user has insufficient ratings or does not exist.
    """
    recs = db.query(Recommendation).filter(Recommendation.username == username).order_by(Recommendation.score.desc()).all()
    if recs:
        sim_users = db.query(UserSimilarity).filter(UserSimilarity.target_username == username).order_by(UserSimilarity.similarity_score.desc()).all()
        
        book_ids = [r.book_id for r in recs]
        books = db.query(Book).filter(Book.id.in_(book_ids)).all()
        score_map = {r.book_id: r.score for r in recs}
        sorted_books = sorted(books, key=lambda book: score_map.get(book.id, 0.0), reverse=True)
        
        return {
            "type": "personalized",
            "top_similar_users": [{"username": s.similar_username, "similarity": s.similarity_score} for s in sim_users],
            "books": [{"id": book.id, "slug": book.slug, "title": book.title, "authors": book.authors, "rating": book.average_rating, "categories": book.categories, "pages": book.page_count, "num_votes": book.num_votes, "description": book.description, "cover_url": book.cover_url} for book in sorted_books]
        }
    
    user_books = books_api.fetch_books_by_username(username)
    if user_books and len([user_book for user_book in user_books if user_book.get("rating") is not None]) >= 5:
        db.merge(User(username=username))
        db.query(UserRating).filter(UserRating.username == username).delete()
        
        for rec in user_books:
            rating_val = rec.get("rating")
            book_data = rec.get("book")
            if book_data and rating_val is not None:
                parsed_book = books_api.parse_book(book_data)
                if parsed_book:
                    if parsed_book.get("num_votes", 0) >= 30:
                        db.merge(Book(
                            id=parsed_book["id"], slug=parsed_book["slug"], title=parsed_book["title"], authors=parsed_book["authors"],
                            categories=parsed_book["categories"], description=parsed_book["description"],
                            average_rating=parsed_book["average_rating"], page_count=parsed_book["page_count"],
                            num_votes=parsed_book.get("num_votes", 0), cover_url=parsed_book.get("cover_url", "")
                        ))
                        db.add(UserRating(username=username, book_id=parsed_book["id"], rating=float(rating_val)))
        db.commit()
        
        top_books, top_users = jobs.calculate_recommendations(db, username)
        if top_books:
            book_ids = [book[0] for book in top_books]
            books = db.query(Book).filter(Book.id.in_(book_ids)).all()
            score_map = {book[0]: book[1] for book in top_books}
            sorted_books = sorted(books, key=lambda book: score_map.get(book.id, 0.0), reverse=True)
            return {
                "type": "personalized",
                "top_similar_users": top_users,
                "books": [{"id": book.id, "slug": book.slug, "title": book.title, "authors": book.authors, "rating": book.average_rating, "categories": book.categories, "pages": book.page_count, "num_votes": book.num_votes, "description": book.description, "cover_url": book.cover_url} for book in sorted_books]
            }

    return JSONResponse(
        status_code=404, 
        content={"message": "Profile not found. You must have at least 5 public book ratings on Hardcover."}
    )
