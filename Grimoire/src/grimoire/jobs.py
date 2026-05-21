from grimoire.models import SessionLocal, Book, UserRating, Recommendation, User, UserSimilarity
from grimoire import books_api
import numpy as np
import polars as pl
users_to_process = []
known_users = set()
user_fetch_offset = 0
MAX_USERS = 25000

def get_known_users():
    global known_users
    db = SessionLocal()
    try:
        known = [user.username for user in db.query(User).all()]
        known_users = set(known)
    finally:
        db.close()

def fetch_new_users():
    global users_to_process, user_fetch_offset, known_users
    if user_fetch_offset > MAX_USERS:
        return
        
    added_count = 0
    while user_fetch_offset <= MAX_USERS and added_count < 100:
        new_users = books_api.fetch_users_list(limit=100, offset=user_fetch_offset)
        if not new_users:
            break
            
        for new_user in new_users:
            if new_user not in users_to_process and new_user not in known_users:
                users_to_process.append(new_user)
                added_count += 1
                
        user_fetch_offset += 100
    print(f"Added {added_count} users to the queue")

def continuous_sync():
    global users_to_process, user_fetch_offset, known_users
    if not users_to_process:
        if user_fetch_offset > MAX_USERS:
            users_to_process.extend(list(known_users))
        return

    username = users_to_process.pop(0)
    known_users.add(username)
    
    db = SessionLocal()
    try:
        user_books = books_api.fetch_books_by_username(username)
        if user_books and len([user_book for user_book in user_books if user_book.get("rating") is not None]) >= 5:
            db.merge(User(username=username))
            for user_book in user_books:
                rating_val = user_book.get("rating")
                book_data = user_book.get("book")
                if book_data and rating_val is not None:
                    parsed_book = books_api.parse_book(book_data)
                    if parsed_book and parsed_book.get("num_votes", 0) >= 30:
                        db.merge(Book(
                            id=parsed_book["id"], slug=parsed_book["slug"], title=parsed_book["title"], authors=parsed_book["authors"],
                            categories=parsed_book["categories"], description=parsed_book["description"],
                            average_rating=parsed_book["average_rating"], page_count=parsed_book["page_count"],
                            num_votes=parsed_book.get("num_votes", 0), cover_url=parsed_book.get("cover_url", "")
                        ))
                        db.merge(UserRating(username=username, book_id=parsed_book["id"], rating=float(rating_val)))
        db.commit()
    finally:
        db.close()

def get_normalized_matrix(db):
    ratings = db.query(UserRating).all()
    if not ratings:
        return pl.DataFrame({"username": []})
        
    books = db.query(Book).all()
    avg_ratings = {book.id: book.average_rating or 2.5 for book in books}
        
    mapped_ratings = []
    for rating_record in ratings:
        # avg = avg_ratings.get(rating_record.book_id, 2.5)
        # centered = rating_record.rating - avg
        # if centered == 0: centered = 1e-9
        # mapped_ratings.append({"username": rating_record.username, "book_id": rating_record.book_id, "rating": centered})
        normalized = (rating_record.rating / 2.5) - 1.0
        if normalized == 0: normalized = 1e-9
        mapped_ratings.append({"username": rating_record.username, "book_id": rating_record.book_id, "rating": normalized})

    df = pl.DataFrame(mapped_ratings)
    matrix = df.pivot(values="rating", index="username", on="book_id", aggregate_function="mean").fill_null(0.0)
    return matrix

def calculate_recommendations(db, username, matrix_df=None):
    ratings = db.query(UserRating).filter(UserRating.username == username).all()
    if not ratings: return [], []
    if matrix_df is None:
        matrix_df = get_normalized_matrix(db)
    if matrix_df.is_empty() or username not in matrix_df["username"].to_list(): return [], []
    
    users = matrix_df["username"].to_list()
    book_ids = matrix_df.columns[1:]
    vectors = matrix_df.drop("username").to_numpy()
    user_idx = users.index(username)
    target_vector = vectors[user_idx]
    
    norms = np.linalg.norm(vectors, axis=1)
    norms[norms == 0] = 1e-9
    target_norm = np.linalg.norm(target_vector) or 1e-9
    cos_sim = np.dot(vectors, target_vector) / (norms * target_norm)
    
    intersections = np.sum((vectors != 0) & (target_vector != 0), axis=1)
    weighted_sim = cos_sim * np.log(intersections + 1)
    
    top_indices = np.argsort(weighted_sim)[::-1]
    top_25 = [idx for idx in top_indices if users[idx] != username][:25]
    if not top_25: return [], []
    
    target_read = set(rating_record.book_id for rating_record in ratings)
    book_scores = {}
    for idx in top_25:
        sim = weighted_sim[idx]
        if sim <= 0: continue
        for book_i, rating in enumerate(vectors[idx]):
            book_id = book_ids[book_i]
            if rating != 0 and book_id not in target_read:
                if book_id not in book_scores: book_scores[book_id] = {"sum": 0.0, "sim_sum": 0.0, "count": 0}
                book_scores[book_id]["sum"] += rating * sim
                book_scores[book_id]["sim_sum"] += sim
                book_scores[book_id]["count"] += 1
                
    final_scores = {book_id: (score_data["sum"] / score_data["sim_sum"]) * np.log(score_data["count"] + 1) for book_id, score_data in book_scores.items()}
    top_books = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:9]
    
    db.query(Recommendation).filter(Recommendation.username == username).delete()
    for book_id, score in top_books:
        db.add(Recommendation(username=username, book_id=book_id, score=score))
        
    db.query(UserSimilarity).filter(UserSimilarity.target_username == username).delete()
    top_sim_users = [{"username": users[idx], "similarity": float(weighted_sim[idx])} for idx in top_25[:9]]
    for sim_user in top_sim_users:
        db.add(UserSimilarity(target_username=username, similar_username=sim_user["username"], similarity_score=sim_user["similarity"]))
        
    db.commit()
    return top_books, top_sim_users

def recalculate_all_recommendations():
    print("Started recalculating recommendations")
    db = SessionLocal()
    try:
        users = [user.username for user in db.query(User).all()]
        matrix_df = get_normalized_matrix(db)
        for username_str in users:
            print(f"Calculated recommendations for {username_str}")
            calculate_recommendations(db, username_str, matrix_df=matrix_df)
    finally:
        db.close()
    print("Finished recalculating recommendations")
