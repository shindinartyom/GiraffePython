import os
import requests

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key.strip()] = val.strip()

HARDCOVER_API_KEY = os.environ.get("HARDCOVER_API_KEY", "")
API_URL = "https://api.hardcover.app/v1/graphql"

def make_headers():
    """Creates HTTP headers for Hardcover API requests.

    Returns:
        dict: A dictionary containing Authorization and Content-Type headers.
    """
    token = HARDCOVER_API_KEY[7:].strip() if HARDCOVER_API_KEY.lower().startswith("bearer ") else HARDCOVER_API_KEY
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def parse_book(item):
    """Parses a dictionary from the Hardcover GraphQL API into a dictionary that matches the Book database model.

    Args:
        item (dict): The raw book object from the GraphQL API response.

    Returns:
        dict or None: A parsed dictionary containing the book's data, or None if item is empty.
    """
    if not item: return None
    title = item.get("title") or "Unknown Title"
    authors_list = item.get("contributions", [])
    authors = ", ".join([c.get("author", {}).get("name") for c in authors_list if c.get("author")]) if authors_list else "Unknown Author"
    
    cats = [t.get("tag") for t in item.get("cached_tags", {}).get("Genre", [])]
    return {
        "id": str(item.get("id")),
        "slug": item.get("slug") or str(item.get("id")),
        "title": title,
        "authors": authors,
        "categories": ",".join(cats) if cats else "Fantasy",
        "description": item.get("description") or "",
        "average_rating": float(item.get("rating") or 4.0),
        "page_count": int(item.get("pages") or 300),
        "num_votes": int(item.get("ratings_count") or item.get("users_count") or 0),
        "cover_url": item.get("image", {}).get("url") if item.get("image") else ""
    }

def fetch_users_list(limit=100, offset=0):
    """Fetches a list of usernames from the Hardcover API, ordered by number of followers.

    Args:
        limit (int, optional): The maximum number of users to fetch. Defaults to 100.
        offset (int, optional): The offset for fetching users. Defaults to 0.

    Returns:
        list of str: A list of usernames. Returns an empty list on failure.
    """
    payload = {
        "query": """query GetUsersList($limit: Int!, $offset: Int!) {
          users(limit: $limit, offset: $offset, order_by: {followers_count: desc}) {
            username
          }
        }""",
        "variables": {"limit": limit, "offset": offset}
    }
    try:
        resp = requests.post(API_URL, json=payload, headers=make_headers(), timeout=10)
        if resp.status_code != 200: return []
        return [u["username"] for u in resp.json().get("data", {}).get("users", []) if u.get("username")]
    except Exception: return []

def fetch_books_by_username(username):
    """Fetches all rated books for a specific user from the Hardcover API.

    Args:
        username (str): The username of the Hardcover user.

    Returns:
        list of dict: A list of user rating objects containing the user's rating and book data.
    """
    payload = {
        "query": """query GetSingleUserRatings($username: citext!) {
          user_books(where: {user: {username: {_eq: $username}}, rating: {_is_null: false}}, limit: 1000) {
            rating
            book { id slug title pages description rating ratings_count cached_tags image { url } contributions { author { name } } }
          }
        }""",
        "variables": {"username": username}
    }
    try:
        resp = requests.post(API_URL, json=payload, headers=make_headers(), timeout=10)
        if resp.status_code != 200: return []
        return resp.json().get("data", {}).get("user_books", [])
    except Exception: return []
