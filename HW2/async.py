import redis
import time
from fastapi import FastAPI

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)

@app.post("/process")
def process_task():
    r.lpush("task_queue", "heavy_task")
    return {"status": "accepted"}

def run_worker():
    while True:
        task = r.brpop("task_queue")
        if task:
            time.sleep(1)
            r.incr("completed_tasks")


if __name__ == "__main__":
    run_worker()
