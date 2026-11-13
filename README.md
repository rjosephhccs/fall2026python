# inventory API

A Python REST API for managing products, stock and orders.

Built with FastAPI, SQLAlchemy and PostgreSQL.

## Python files:

- **main.py**: endpoints for products, stock and orders.
- **schemas.py**: fields accepted in request JSON.
- **database.py**: connection, get_db(), rollback on SQL errors and session cleanup.
- **auth.py**: endpoints for products, stock and orders.
- **requirement.txt**: python dependencies.
- **.env.example**: local configuration template without secrets.
- **.gitignore*: excludes private configuration and generated files.

SQLAlchemy is used for connections, sessions, and parameterized SQL. This service does not define ORM models or create database tables.

## Prepare PostgreSQL

Start PostgreSQL and install the database team's schema, including migrations V001, V002, and V003. 

Follow the database team's [setup instructions](https://github.com/rjosephhccs/fall2026database/blob/main/docs/SETUP.md).

In DBeaver, connect using the Python service login and confirm this works:

```sql
SELECT user_id, username, role, is_active
FROM public.users;
```

The local example database is `inventory_management_dev`. You can use your own database name and password in `.env`.

## Start Java authentication

Configure the Java service to use the same database and start it using the Java team's instructions. For the local setup described here, Java runs at `http://localhost:8081`.

The Python integration expects these Java endpoints:

| Method | Path | Request | Successful response |
| --- | --- | --- | --- |
| POST | `/auth/authenticate` | JSON: `username`, `password` | JWT as plain text |
| POST | `/auth/validate` | Form field: `token` | Validated username as plain text |


## Setup on Windows

Open a terminal inside the API folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your PostgreSQL connection settings and local password:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inventory_management_dev
DB_USER=inventory_python_login
DB_PASSWORD=REPLACE_WITH_YOUR_LOCAL_PASSWORD
JAVA_AUTH_URL=http://localhost:8081
```

## Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs.

Select an endpoint, click **Try it out**, enter the values and click **Execute**.

## Log in using Postman

Create a POST request to `http://localhost:8081/auth/authenticate`.

Choose **Body → raw → JSON**, then enter your own credentials:

```json
{
  "username": "YOUR_USERNAME",
  "password": "YOUR_PASSWORD"
}
```
A successful login returns `200 OK` and a JWT. Copy the token without quotes or extra spaces. Do not share or commit the token.

For a Python API request, open **Authorization → Bearer Token** in Postman and paste the token. First try:

```text
GET http://localhost:8000/api/me
```

## Test the endpoints

Use a local development database: these tests write real records and completed orders cannot be deleted through normal operations.

1. **Create a product:** POST `/api/products` with:

   ```json
   {
     "name": "USB Mouse",
     "sku": "TEST-MOUSE-001",
     "description": "Local API test",
     "price": 10.50,
     "reorder_level": 5
   }
   ```

   Expect 201. Save the returned `product_id`. Initial stock is zero.

2. **Read products:** GET `/api/products` and GET `/api/products/{product_id}` using the returned ID. Expect 200 and the saved details.

3. **Update details:** PUT `/api/products/{product_id}` with:

   ```json
   {
     "name": "USB Mouse - Updated",
     "description": "Updated through FastAPI",
     "price": 10.50,
     "reorder_level": 5
   }
   ```

   Expect 200. This changes product details, not stock or SKU.

4. **Add stock:** POST `/api/stock-transactions` with the actual product ID:

   ```json
   {
     "product_id": 1,
     "transaction_type": "IN",
     "quantity": 10,
     "notes": "Initial stock for local test"
   }
   ```

   Replace `1` with your returned product ID. Expect 201; GET the product again to confirm stock is 10. `OUT` removes units; `ADJUSTMENT` sets the absolute stock count.

5. **Create an order:** switch to the PRODUCT_MANAGER token, verify `/api/me`, and POST `/api/orders` with:

   ```json
   {
     "items": [
       {"product_id": 1, "quantity": 3}
     ]
   }
   ```

   Replace `1` with the actual product ID. Expect 201 and a returned order ID.

## Error responses
- `401`: invalid/expired token or inactive employee.
- `403`: unauthorized user attempting to create an order.
- `404`: product or order not found.
- `409`: database rejected the operation, such as insufficient stock.
- `422`: empty order items, duplicate product IDs, negative quantity, or invalid request fields.
- `503`: database connection unavailable or Java unreachable.

## Current status

This version is for local testing. Python sends the token to Java for validation, then looks up the employee's current ID, role, and active status using V003's four permitted fields. The full live workflow must still be checked on the team's machines.
