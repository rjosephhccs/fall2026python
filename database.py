"""Database connection only. Your existing PostgreSQL schema is unchanged."""
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy import create_engine, URL
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

load_dotenv()

url = URL.create(
    'postgresql+psycopg',
    username=os.getenv('DB_USER', 'inventory_python_login'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '5432')),
    database=os.getenv('DB_NAME', 'inventory_management_dev'),
)
engine = create_engine(url, connect_args={'connect_timeout': 5})
SessionLocal = sessionmaker(bind=engine)

# FastAPI opens a session for each request and closes it afterward.
def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError:
        db.rollback()
        raise HTTPException(503, 'Cannot connect to PostgreSQL. Check your .env.') from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Duplicate record, invalid values or missing related record.') from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(409, 'Database rejected the operation. Check product, stock and order status.') from None
    finally:
        db.close()
