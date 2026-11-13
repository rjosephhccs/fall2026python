"""Local learning version. Java authentication is NOT connected yet."""
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from auth import CurrentUser, get_current_user, require_roles
from schemas import ProductCreate, ProductUpdate, OrderCreate, StockAdd


app = FastAPI(
    title="Electronics IMS - Python Inventory Microservice",
    dependencies=[Depends(get_current_user)]
)

# Allow the local Angular development server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:4200', 'http://127.0.0.1:4200'],
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'PUT'],
    allow_headers=['Content-Type', 'Authorization'],
)

#===========================AUTHENTICATION=========================================
# Temporary user class for local testing. Replace with Java authentication later.
inventory_editor = require_roles('SUPER_USER', 'INVENTORY_MANAGER')
order_creator = require_roles('PRODUCT_MANAGER')


@app.get('/api/me')
def get_me(user: CurrentUser = Depends(get_current_user)):
    return {'user_id': user.user_id, 'username': user.username, 'role': user.role}


#===========================PRODUCTS============================================
# GET all products, limited to 100 for demo purposes
@app.get('/api/products')
def get_products(db: Session = Depends(get_db)):
    query = text('SELECT * FROM public.products ORDER BY product_id LIMIT 100')
    return db.execute(query).mappings().all()


# GET a single product by ID
@app.get('/api/products/{product_id}')
def get_product(product_id: int, db: Session = Depends(get_db)):
    query = text('SELECT * FROM public.products WHERE product_id = :id')
    product = db.execute(query, {'id': product_id}).mappings().first()
    if product is None:
        raise HTTPException(404, 'Product not found')
    return product


# POST a new product. Stock is set to 0 by default. Reorder level is optional.
@app.post('/api/products', status_code=201, dependencies=[Depends(inventory_editor)])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    query = text('SELECT public.create_product(:name, :sku, :description, :price, :reorder_level)')
    product_id = db.execute(query, product.model_dump()).scalar_one()
    db.commit()
    return {'message': 'Product created', 'product_id': product_id}


# PUT an existing product. Stock is unchanged at this step.
@app.put('/api/products/{product_id}', dependencies=[Depends(inventory_editor)])
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    query = text('SELECT public.update_product_details(:id, :name, :description, :price, :reorder_level)')
    values = product.model_dump()
    values['id'] = product_id
    db.execute(query, values)
    db.commit()
    return {'message': 'Product updated'}


#=============================TRANSACTIONS==================================================
# POST a stock transaction. Sales also deduct stock through orders.
@app.post('/api/stock-transactions', status_code=201, dependencies=[Depends(inventory_editor)])
def change_stock(stock: StockAdd, db: Session = Depends(get_db)):
    query = text('SELECT public.record_stock_transaction(:product_id, :transaction_type, :quantity, :notes)')
    transaction_id = db.execute(query, stock.model_dump()).scalar_one()
    db.commit()
    return {'message': 'Stock updated', 'transaction_id': transaction_id}


#===================================ORDERS====================================================
# GET a single order with its items. Completed orders show the total amount.
@app.get('/api/orders/{order_id}')
def get_order(order_id: int, db: Session = Depends(get_db)):
    query = text('SELECT * FROM public.orders WHERE order_id = :id')
    order = db.execute(query, {'id': order_id}).mappings().first()
    if order is None:
        raise HTTPException(404, 'Order not found')
    query = text('SELECT * FROM public.order_items WHERE order_id = :id ORDER BY order_item_id')
    items = db.execute(query, {'id': order_id}).mappings().all()
    return {'order': order, 'items': items}

# POST endpoint to create a new order
@app.post('/api/orders', status_code=201)
def create_order(order: OrderCreate, user: CurrentUser = Depends(order_creator), db: Session = Depends(get_db)):
    temp_user_id = 1  # temporary ID user fo PRODUCT MANAGER

    # Create the order.
    query = text('SELECT public.create_pending_order(:user_id)')
    order_id = db.execute(query, {
        'user_id': temp_user_id
    }).scalar_one()

    # Add the products.
    for item in order.items:
        query = text(
            'SELECT public.add_order_item(:order_id, :product_id, :quantity)'
        )
        db.execute(query, {
            'order_id': order_id,
            'product_id': item.product_id,
            'quantity': item.quantity
        })

    # Complete the sale and deduct stock.
    query = text('SELECT public.complete_order(:order_id)')
    total = db.execute(query, {'order_id': order_id}).scalar_one()

    db.commit()

    return {
        'message': 'Sale completed',
        'order_id': order_id,
        'total_amount': total
    }




