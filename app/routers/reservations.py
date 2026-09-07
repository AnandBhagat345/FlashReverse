from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Reservation
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
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
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

    product.available_stock -= reservation.quantity

    new_reservation = Reservation(
        product_id=product.id,
        quantity=reservation.quantity,
        status="confirmed"
    )

    db.add(new_reservation)

    db.commit()

    db.refresh(new_reservation)

    return new_reservation