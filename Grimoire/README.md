# Grimoire

Grimoire is a book recommendation engine built with Python, FastAPI, Polars, and SQLite. It interacts with the Hardcover GraphQL API to build a localized database of readers and their book ratings, using collaborative filtering to generate highly personalized recommendations. Frontend is written by AI.

## Features

- **Continuous Data Ingestion**: A background job queue continuously scrapes the Hardcover API to fetch new users and their book ratings into a local SQLite database.
- **Collaborative Filtering**: The engine calculates Cosine Similarity between users to accurately measure true preference. Similarities are weighted by the number of books read in common.
- **Database Caching**: The heavy matrix math is precalculated in the background periodically. The FastAPI endpoints instantly serve cached recommendations and similar-user profiles directly from the SQLite database.

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
uv run uvicorn grimoire.main:app --reload
```

### 4. Running the Frontend
In a separate terminal, serve the static web application:
```bash
cd frontend
python -m http.server 3000
```
Visit `http://localhost:3000` in your browser. Enter a Hardcover username to instantly view their top similar users and personalized book recommendations.
