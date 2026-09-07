from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routers import products
from app.routers import reservations


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="FlashReserve API",
    description="Concurrency-Safe Inventory Reservation System",
    version="1.0.0"
)


app.include_router(products.router)
app.include_router(reservations.router)


@app.get("/")
def health_check():
    return {
        "message": "FlashReserve API is running"
    }