from pydantic import BaseModel, Field
from datetime import datetime


class ProductCreate(BaseModel):
    name: str
    available_stock: int = Field(gt=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    available_stock: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReservationCreate(BaseModel):
    quantity: int = Field(gt=0)


class ReservationResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True