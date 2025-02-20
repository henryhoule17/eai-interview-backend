# Endeavor Interview Project - Backend

This is the backend service for the PDF extraction and matching application. It's built with FastAPI and PostgreSQL.

## Prerequisites

- Python 3.12+
- PostgreSQL
- Docker (optional)

## Local Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL:
   ```bash
   # Run PostgreSQL container
   docker run --name endeavor-postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_DB=orders \
     -p 5432:5432 \
     -d postgres:alpine
   ```

4. Run the server:
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

## Docker Setup

1. Build the container:
   ```bash
   docker build -t endeavor-backend .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name endeavor-api \
     -p 8000:8000 \
     -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/orders \
     endeavor-backend
   ```

## API Endpoints

- `POST /extract`: Extract data from PDF files
- `POST /match`: Match extracted items with database
- `POST /finalize`: Submit final order
- `GET /orders`: List all orders

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/orders`)
- `NEXT_PUBLIC_BACKEND_URL`: Backend URL for frontend (default: `http://localhost:8000`)

## Development

- API documentation available at: http://localhost:8000/docs
- OpenAPI spec at: http://localhost:8000/openapi.json

## Database Schema

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR,
    customer_id VARCHAR,
    name VARCHAR,
    quantity FLOAT,
    price FLOAT,
    total FLOAT
);
```
