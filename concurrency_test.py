import requests
import time
import uuid

from concurrent.futures import ThreadPoolExecutor


URL = "http://127.0.0.1:8000/products/10/reserve"


def reserve_ticket():
    response = requests.post(
        URL,
        json={"quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    return response.status_code


TOTAL_REQUESTS = 50
MAX_WORKERS = 10

start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

    futures = []

    for i in range(TOTAL_REQUESTS):
        future = executor.submit(reserve_ticket)
        futures.append(future)

    results = []

    for future in futures:
        results.append(future.result())


end_time = time.time()

total_time = end_time - start_time

successful = 0
failed = 0

for status_code in results:

    if status_code == 201:
        successful += 1

    elif status_code == 400:
        failed += 1
        
    else :
        other +=1


print("\n===== LOAD TEST RESULT =====")

print("Total Requests:", TOTAL_REQUESTS)
print("Successful:", successful)
print("Failed:", failed)
print("Total Time:", round(total_time, 4), "seconds")

if total_time > 0:
    requests_per_second = TOTAL_REQUESTS / total_time
    print("Requests/sec:", round(requests_per_second, 2))