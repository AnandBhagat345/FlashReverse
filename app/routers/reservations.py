from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import time

from app.database import get_db
from app.models import Product, Reservation,IdempotencyRecord
from app.schemas import (
    ReservationCreate,
    ReservationResponse
)


router = APIRouter(
    prefix="/products",
    tags=["Reservations"]
)


@router.post(
    "/{product_id}/reserve",
    response_model=ReservationResponse,
    status_code=201
)
def reserve_product(
    product_id: int,
    reservation: ReservationCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
        print("IDEMPOTENCY KEY:", idempotency_key)

    # try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        if product.available_stock < reservation.quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock"
            )

        time.sleep(1)

        product.available_stock -= reservation.quantity

        new_reservation = Reservation(
            product_id=product.id,
            quantity=reservation.quantity,
            status="confirmed"
        )

        db.add(new_reservation)
        
        # print("BEFORE EXCEPTION")

        # ROLLBACK TEST
        # raise Exception("Something went wrong!")

        db.commit()

        db.refresh(new_reservation)

        return new_reservation

    # except Exception as e:
    #     print("EXCEPTION CAUGHT:", e)
    #     db.rollback()
    #     print("RollBack Executes")
    #     raise