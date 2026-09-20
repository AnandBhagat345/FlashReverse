import asyncio
import time


async def task(name):
    print(name, "started")

    time.sleep(2)

    print(name, "finished")


async def main():

    start = time.time()

    await asyncio.gather(
        task("Task 1"),
        task("Task 2"),
        task("Task 3")
    )

    end = time.time()

    print("Total Time:", round(end - start, 2), "seconds")


asyncio.run(main())