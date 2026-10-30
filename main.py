from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from schemas import ProductCreate, ProductUpdate, OrderCreate, OrderItemAdd

app = FastAPI(title="Electronics IMS - Python Inventory Microservice")

@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        query = text("SELECT public.create_product(:name, :sku, :description, :price, :reorder_level)")
        result = db.execute(query, {
            "name": product.name, "sku": product.sku, "description": product.description,
            "price": product.price, "reorder_level": product.reorder_level
        }).scalar()
        db.commit()
        return {"message": "Product created", "product_id": result}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    try:
        query = text("SELECT public.update_product_details(:p_id, :name, :description, :price, :reorder_level)")
        db.execute(query, {
            "p_id": product_id, "name": product.name, "description": product.description,
            "price": product.price, "reorder_level": product.reorder_level
        })
        db.commit()
        return {"message": "Product updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders", status_code=201)
def create_pending_order(order: OrderCreate, db: Session = Depends(get_db)):
    temp_user_id = 1
    try:
        query = text("SELECT public.create_pending_order(:user_id, :notes)")
        result = db.execute(query, {"user_id": temp_user_id, "notes": order.notes}).scalar()
        db.commit()
        return {"message": "Pending order created", "order_id": result}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/{order_id}/items")
def add_order_item(order_id: int, item: OrderItemAdd, db: Session = Depends(get_db)):
    try:
        query = text("SELECT public.add_order_item(:order_id, :product_id, :quantity)")
        result = db.execute(query, {"order_id": order_id, "product_id": item.product_id, "quantity": item.quantity}).scalar()
        db.commit()
        return {"message": "Item added", "order_item_id": result}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/{order_id}/complete")
def complete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        query = text("SELECT public.complete_order(:order_id)")
        total_amount = db.execute(query, {"order_id": order_id}).scalar()
        db.commit()
        return {"message": "Order completed", "total_amount": total_amount}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))