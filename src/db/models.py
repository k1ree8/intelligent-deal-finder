from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Ad(Base):
    """
    Data model for storing information about an ad from Avito.
    """
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    avito_id = Column(BigInteger, unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    price = Column(Integer, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    seller_name = Column(String(100), nullable=True)
    delivery_available = Column(Boolean, default=False)
    parameters = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Ad(id={self.id}, title='{self.title[:30]}...')>"


if __name__ == "__main__":
    from src.db.session import engine

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")