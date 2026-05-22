# Grimoire

Grimoire is a book recommendation engine built with Python, FastAPI, Polars, and SQLite. It interacts with the Hardcover GraphQL API to build a localized database of readers and their book ratings, using collaborative filtering to generate highly personalized recommendations. Frontend is written by AI.

## Features

- **Continuous Data Ingestion**: A background job queue continuously scrapes the Hardcover API to fetch new users and their book ratings into a local SQLite database.
- **Collaborative Filtering**: The engine calculates Cosine Similarity between users to accurately measure true preference. Similarities are weighted by the number of books read in common.
- **Database Caching**: The heavy matrix math is precalculated in the background periodically. The FastAPI endpoints instantly serve cached recommendations and similar-user profiles directly from the SQLite database.

## Technical Implementation
This project was designed to meet high-concurrency and batch-processing requirements:

- **Decoupled Entities**: The system maintains strict separation between the Book Catalog (`Book` model), User Events/Ratings (`UserRating` model), and the calculated results (`Recommendation` and `UserSimilarity` models).
- **Asynchronous Batch Processing**: Recommendations are precalculated and cached for all users in the database. A background `APScheduler` worker recalculates the entire recommendation matrix periodically in batch mode. The API simply performs an O(1) lookup of precalculated results, ensuring instant response times.
- **Non-Blocking API & WAL Mode**: To ensure that heavy background batch-recalculations do not block the main FastAPI endpoints, the SQLite database is configured with Write-Ahead Logging. This allows the API to seamlessly read recommendations while the background worker is writing new ones, completely eliminating database lock contention.
- **Expected Load & Matrix Math**: The application continuously syncs a queue of up to 25,000 users. To handle the dense matrix math efficiently without bogging down Python, the raw ratings are pivoted into a dense Polars DataFrame. Cosine similarity and vector intersections are calculated via NumPy and Polars, making the background batch process fast. It recalculates recommendations approximately for 3 users a second.

## Setup & Execution

### 1. Installation
This project uses `uv` as its package manager.

Install `uv` globally (if you don't have it):
```bash
pip install uv
```

Clone the repository and sync the virtual environment:
```bash
uv sync
```

### 2. Environment Variables
Create a `.env` file in the root directory and add your Hardcover API Key:
```env
HARDCOVER_API_KEY=Bearer your_api_key_here
```

### 3. Running the Engine
The core engine relies on the FastAPI background scheduler to sync data. Start the backend server using `uv run`:
```bash
uv run uvicorn grimoire.main:app
```

### 4. Running the Frontend
In a separate terminal, serve the static web application:
```bash
cd frontend
python -m http.server 3000
```
Visit `http://localhost:3000` in your browser. Enter a Hardcover username to instantly view their top similar users and personalized book recommendations.
