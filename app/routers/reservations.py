from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import time

from app.database import get_db
from app.models import Product, Reservation, IdempotencyRecord
from app.schemas import ReservationCreate, ReservationResponse


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

    # 1. Lock the product row
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

    # 2. Check if idempotency key already exists
    existing_record = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.key == idempotency_key
        )
        .first()
    )

    if existing_record:

        # Same key but different request details
        if (
            existing_record.product_id != product_id
            or existing_record.quantity != reservation.quantity
        ):
            raise HTTPException(
                status_code=400,
                detail="Idempotency-Key already used with different request details"
            )

        # Same key and same request details
        existing_reservation = (
            db.query(Reservation)
            .filter(
                Reservation.id == existing_record.reservation_id
            )
            .first()
        )

        if existing_reservation:
            return existing_reservation

        raise HTTPException(
            status_code=404,
            detail="Reservation linked to idempotency key not found"
        )

    # 3. Check stock
    if product.available_stock < reservation.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    # Simulate processing delay
    time.sleep(1)

    # 4. Decrease stock
    product.available_stock -= reservation.quantity

    # 5. Create reservation
    new_reservation = Reservation(
        product_id=product.id,
        quantity=reservation.quantity,
        status="confirmed"
    )

    db.add(new_reservation)

    # Get reservation ID before creating idempotency record
    db.flush()

    # 6. Create idempotency record
    idempotency_record = IdempotencyRecord(
        key=idempotency_key,
        product_id=product.id,
        quantity=reservation.quantity,
        reservation_id=new_reservation.id
    )

    db.add(idempotency_record)

    # 7. Commit transaction
    try:
        db.commit()

    except IntegrityError:

        # Duplicate idempotency key
        db.rollback()

        existing_record = (
            db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.key == idempotency_key
            )
            .first()
        )

        if not existing_record:
            raise HTTPException(
                status_code=500,
                detail="Failed to create idempotency record"
            )

        # Same key but different request
        if (
            existing_record.product_id != product_id
            or existing_record.quantity != reservation.quantity
        ):
            raise HTTPException(
                status_code=400,
                detail="Idempotency-Key already used with different request details"
            )

        # Return original reservation
        existing_reservation = (
            db.query(Reservation)
            .filter(
                Reservation.id == existing_record.reservation_id
            )
            .first()
        )

        if existing_reservation:
            return existing_reservation

        raise HTTPException(
            status_code=404,
            detail="Reservation linked to idempotency key not found"
        )

    # 8. Refresh and return newly created reservation
    db.refresh(new_reservation)

    return new_reservation


@router.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):

    # 1. Find reservation
    reservation = (
        db.query(Reservation)
        .filter(Reservation.id == reservation_id)
        .first()
    )

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    # 2. Prevent duplicate cancellation
    if reservation.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Reservation already cancelled"
        )

    # 3. Lock product row
    product = (
        db.query(Product)
        .filter(Product.id == reservation.product_id)
        .with_for_update()
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 4. Restore stock
    product.available_stock += reservation.quantity

    # 5. Update reservation status
    reservation.status = "cancelled"

    # 6. Commit transaction
    db.commit()

    db.refresh(reservation)

    return {
        "message": "Reservation cancelled successfully",
        "reservation_id": reservation.id,
        "status": reservation.status,
        "restored_quantity": reservation.quantity,
        "available_stock": product.available_stock
    }