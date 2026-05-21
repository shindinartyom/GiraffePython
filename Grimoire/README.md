# Grimoire

Grimoire is a book recommendation engine built with Python, FastAPI, Polars, and SQLite. It interacts with the Hardcover GraphQL API to build a localized database of readers and their book ratings, using mean-centered collaborative filtering to generate highly personalized recommendations. Frontend is written by AI.

## Features

- **Continuous Data Ingestion**: A background job queue continuously scrapes the Hardcover API to fetch new users and their book ratings into a local SQLite database.
- **Mean-Centered Collaborative Filtering**: The engine calculates Cosine Similarity between users, mean-centering their ratings against global book averages to accurately measure true preference. Similarities are weighted by the number of books read in common.
- **Database Caching**: The heavy matrix math is precalculated in the background periodically. The FastAPI endpoints instantly serve cached recommendations and similar-user profiles directly from the SQLite database.

## Setup & Execution

### 1. Installation
Install the project dependencies (preferably inside a virtual environment):
```bash
pip install -r requirements.txt
pip install -e .
```

### 2. Environment Variables
Create a `.env` file in the root directory and add your Hardcover API Key:
```env
HARDCOVER_API_KEY=Bearer your_api_key_here
```

### 3. Running the Engine
The core engine relies on the FastAPI background scheduler to sync data. Start the backend server:
```bash
uvicorn grimoire.main:app --reload
```

### 4. Running the Frontend
In a separate terminal, serve the static web application:
```bash
cd frontend
python -m http.server 3000
```
Visit `http://localhost:3000` in your browser. Enter a Hardcover username to instantly view their top similar users and personalized book recommendations.
