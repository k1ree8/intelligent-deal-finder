from sqlalchemy.orm import Session
from src.db import models


def get_ads(db: Session, skip: int = 0, limit: int = 100) -> list[models.Ad]:
    """
    Retrieves a list of ads from a paginated database.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip for pagination. Default is 0.
        limit (int): The maximum number of records to return. Default is 100.

    Returns:
        A list of Ad ORM objects.
    """
    return (
        db.query(models.Ad)
        .order_by(models.Ad.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
