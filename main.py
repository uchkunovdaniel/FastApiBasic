from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Car(Base):
    __tablename__ = "Cars"

    Id: Mapped[int] = mapped_column(primary_key=True)
    Brand: Mapped[str] = mapped_column(String(50))
    Model: Mapped[str] = mapped_column(String(50))
    Horsepower: Mapped[int]


class CarIn(BaseModel):
    Brand: str = Field(max_length=50)
    Model: str = Field(max_length=50)
    Horsepower: int = Field(gt=0)


class CarUpdate(BaseModel):
    Brand: str | None = Field(default=None, max_length=50)
    Model: str | None = Field(default=None, max_length=50)
    Horsepower: int | None = Field(default=None, gt=0)


class CarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    Brand: str
    Model: str
    Horsepower: int


Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    with SessionLocal() as db:
        yield db


@app.get("/",  response_model=list[CarOut])
def root(db: Session = Depends(get_db)):
    return db.scalars(select(Car)).all()


@app.get("/{carId}", response_model=CarOut)
def get_car(carId: int, db: Session = Depends(get_db)):
    car = db.get(Car, carId)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@app.post("/", response_model=CarOut, status_code=201)
def create_car(car: CarIn, db: Session = Depends(get_db)):
    db_car = Car(**car.model_dump())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car


@app.delete("/{carId}", status_code=204)
def delete_car(carId: int, db: Session = Depends(get_db)):
    car = db.get(Car, carId)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    db.delete(car)
    db.commit()


@app.put("/{carId}", response_model=CarOut)
def update_car(carId: int, car: CarIn, db: Session = Depends(get_db)):
    db_car = db.get(Car, carId)
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    for key, value in car.model_dump().items():
        setattr(db_car, key, value)
    db.commit()
    db.refresh(db_car)
    return db_car


@app.patch("/{carId}", response_model=CarOut)
def patch_car(carId: int, car: CarUpdate, db: Session = Depends(get_db)):
    db_car = db.get(Car, carId)
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    for key, value in car.model_dump(exclude_unset=True).items():
        setattr(db_car, key, value)
    db.commit()
    db.refresh(db_car)
    return db_car

