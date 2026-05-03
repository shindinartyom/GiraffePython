import time
import redis
from fastapi import FastAPI

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)

@app.post("/process")
def process_task():
    time.sleep(1)
    r.incr("completed_tasks")
    return {"status": "done"}
