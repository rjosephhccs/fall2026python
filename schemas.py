from pydantic import BaseModel, Field
from typing import Optional

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sku: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    reorder_level: int = Field(default=10, ge=0)

class ProductUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    reorder_level: int = Field(..., ge=0)

class OrderCreate(BaseModel):
    notes: Optional[str] = None

class OrderItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)