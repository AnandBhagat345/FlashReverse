import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8000/products/11/reserve"

HEADERS = {
    "Idempotency-Key": "TEST-KEY-002"
}

DATA = {
    "quantity": 1
}

def reserve_product():
    response = requests.post(
        URL,
        json={"quantity": 1},
        headers=HEADERS
    )

    return response.status_code, response.text


TOTAL_REQUESTS = 10
MAX_WORKERS = 10

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = []

    for i in range(TOTAL_REQUESTS):
        future = executor.submit(reserve_product)
        futures.append(future)

    for future in futures:
        print(future.result())