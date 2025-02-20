from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import requests
import httpx
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/orders')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    customer_id = Column(String)
    name = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    total = Column(Float)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load environment variables
load_dotenv()

# Get frontend URL from environment variable, default to localhost:3000
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractedItem(BaseModel):
    Request_Item: str | None = None
    Amount: float | None = None
    Unit_Price: float | None = None
    Total: float | None = None

class MatchResult(BaseModel):
    match: str | None = None
    score: float | None = None

class BatchMatchResponse(BaseModel):
    results: Dict[str, List[MatchResult]]

class BatchMatchRequest(BaseModel):
    queries: List[str]

class FinalizeItems(BaseModel):
    items: List[ExtractedItem]

class OrderItem(BaseModel):
    name: str
    quantity: float
    price: float
    total: float

class FinalizeRequest(BaseModel):
    customerName: str
    customerId: str
    items: List[OrderItem]

@app.post("/match")
async def match_texts(queries: List[str] | str, limit: int = 5) -> BatchMatchResponse:
    """
    Endpoint to match queries against the product database using batch API
    """
    try:
        # Convert single query to list if needed
        query_list = queries if isinstance(queries, list) else [queries]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://endeavor-interview-api-gzwki.ondigitalocean.app/match/batch",
                params={"limit": limit},
                headers={"Content-Type": "application/json"},
                json={"queries": query_list}
            )
            response.raise_for_status()
            
            response_data = response.json()
            return BatchMatchResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract", response_model=List[ExtractedItem])
async def extract_info(file: UploadFile = File(...)) -> List[ExtractedItem]:
    """
    Endpoint to extract information from uploaded PDF file
    """
    print("Recieved file")
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        # Read the file content
        print("Reading file")
        file_content = await file.read()

        # Send the PDF to the extraction API
        files = {'file': (file.filename, file_content, 'application/pdf')}
        headers = {
            'accept': 'application/json'
        }
        print("Sending request")
        response = requests.post(
            'https://plankton-app-qajlk.ondigitalocean.app/extraction_api',
            headers=headers,
            files=files
        )
        print("Request sent. response: ", response.json())

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error from extraction service"
            )

        # Parse the response into the correct format
        items = []
        for item in response.json():
            items.append(ExtractedItem(
                Request_Item=item.get('Request Item', None),
                Amount=item.get('Amount', None),
                Unit_Price=item.get('Unit Price', None),
                Total=item.get('Total', None),
            ))

        print("Returning value: ", items)
        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finalize")
async def finalize_order(request: FinalizeRequest, db: Session = Depends(get_db)):
    try:
        # Create orders (one row per item)
        order_ids = []
        for item in request.items:
            db_order = Order(
                customer_name=request.customerName,
                customer_id=request.customerId,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
                total=item.total
            )
            db.add(db_order)
            db.flush()
            order_ids.append(db_order.id)
        
        # Commit all changes
        db.commit()
        
        return {
            "status": "success",
            "message": "Orders saved successfully",
            "orderIds": order_ids
        }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders")
async def get_orders(db: Session = Depends(get_db)):
    try:
        orders = db.query(Order).all()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
