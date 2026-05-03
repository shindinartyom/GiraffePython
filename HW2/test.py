import time
import httpx
import asyncio
import redis

URL = "http://127.0.0.1:8000/process"
TIMEOUT = 150.0
r_conn = redis.Redis(host='localhost', port=6379, db=0)

def test_sequential(count):
    r_conn.set("completed_tasks", 0)
    start = time.time()
    
    with httpx.Client() as client:
        for _ in range(count):
            client.post(URL, timeout=TIMEOUT)
    
    api_time = time.time() - start
    print(f"API Response Time ({count}): Time={api_time:.2f}s, Avg={api_time/count:.4f}s")

    while int(r_conn.get("completed_tasks") or 0) < count:
        time.sleep(0.1)
    
    total_time = time.time() - start
    print(f"Processing Time ({count}): Time={total_time:.2f}s, Avg={total_time/count:.4f}s")

async def test_parallel(count):
    r_conn.set("completed_tasks", 0)
    start = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = [client.post(URL, timeout=TIMEOUT) for _ in range(count)]
        await asyncio.gather(*tasks)
    
    api_time = time.time() - start
    print(f"API Response Time ({count}): Time={api_time:.2f}s, Avg={api_time/count:.4f}s")

    while int(r_conn.get("completed_tasks") or 0) < count:
        await asyncio.sleep(0.1)
    
    total_time = time.time() - start
    print(f"Processing Time ({count}): Time={total_time:.2f}s, Avg={total_time/count:.4f}s")

def main():
    print("===== SEQUENTIAL =====")
    for num_requests in [10, 50, 100]:
        test_sequential(num_requests)
    
    print("\n===== PARALLEL =====")
    num_requests = 20
    asyncio.run(test_parallel(num_requests))

if __name__ == "__main__":
    main()
