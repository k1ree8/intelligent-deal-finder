from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from . import crud, schemas
from src.db.session import SessionLocal

router = APIRouter(
    prefix="/ads",
    tags=["ads"],
)


# --- Dependency ---
def get_db():
    """
    A dependency that creates and provides a DATABASE session for each request.
    Ensures that the session is closed after the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.AdRead])
def read_ads(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Getting a list of paginated ads.
    - **skip**: The number of skipped entries.
    - **limit**: The maximum number of entries.
    """
    ads = crud.get_ads(db=db, skip=skip, limit=limit)
    return ads
