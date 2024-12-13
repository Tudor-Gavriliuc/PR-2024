from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from crud import get_cars
from database_model.models import SessionLocal

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/cars/")
def list_cars(offset: int = Query(0), limit: int = Query(10), db: Session = Depends(get_db)):
    return get_cars(db, offset=offset, limit=limit)
