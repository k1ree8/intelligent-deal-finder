from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Ad(Base):
    """
    Финальная, очищенная модель данных для хранения объявлений.
    Содержит только те поля, которые мы реально парсим и используем.
    """
    __tablename__ = 'ads'

    avito_id = Column(BigInteger, primary_key=True, unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)

    title = Column(String(255), nullable=False)
    price = Column(Integer, nullable=True) 
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    condition = Column(String(50), nullable=True)
    model = Column(String(255), nullable=True, index=True)
    memory = Column(String(255), nullable=True, index=True)
    seller_name = Column(String(255), nullable=True)
    seller_rating = Column(Float, nullable=True)
    seller_reviews_count = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Ad(id={self.avito_id}, title='{self.title[:30]}...')>"

if __name__ == "__main__":
    from src.db.session import engine

    print("Создаем/обновляем таблицы в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы/обновлены.")