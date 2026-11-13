from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sku: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    price: Decimal = Field(
        ..., ge=0, max_digits=10,
        decimal_places=2, allow_inf_nan=False
    )
    reorder_level: int = Field(default=10, ge=0)


class ProductUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(
        ..., ge=0, max_digits=10,
        decimal_places=2, allow_inf_nan=False
    )
    reorder_level: int = Field(..., ge=0)


class OrderCreate(BaseModel):
    items: list[OrderItemAdd] = Field(min_length=1)

    @model_validator(mode='after')
    def check_products(self):
        ids = [item.product_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError(
                'Include each product once with its total quantity'
            )
        return self


class StockAdd(BaseModel):
    product_id: int = Field(gt=0, le=2147483647, strict=True)
    transaction_type: Literal['IN', 'OUT', 'ADJUSTMENT']
    quantity: int = Field(ge=0, le=2147483647, strict=True)
    notes: Optional[str] = None

    @model_validator(mode='after')
    def check_quantity(self):
        if self.transaction_type in ('IN', 'OUT') and self.quantity == 0:
            raise ValueError(
                'IN and OUT require a quantity greater than zero'
            )
        return self