from sqlalchemy.orm import Session
from models import Car

def get_cars(db: Session, offset: int, limit: int):
    return db.query(Car).offset(offset).limit(limit).all()

def get_car_by_id(db: Session, car_id: int):
    return db.query(Car).filter(Car.id == car_id).first()

def create_car(db: Session, car_data: dict):
    new_car = Car(**car_data)
    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return new_car

def update_car(db: Session, car_id: int, car_data: dict):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        return None
    for key, value in car_data.items():
        setattr(car, key, value)
    db.commit()
    return car

def delete_car(db: Session, car_id: int):
    car = db.query(Car).filter(Car.id == car_id).first()
    if car:
        db.delete(car)
        db.commit()
    return car
