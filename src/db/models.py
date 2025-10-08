# src/db/models.py

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
from sqlalchemy.sql import func

Base = declarative_base()

class Ad(Base):
    """
    Финальная, очищенная модель данных для хранения объявлений.
    Содержит только те поля, которые мы реально парсим и используем.
    """
    __tablename__ = 'ads'

    # Основные идентификаторы
    avito_id = Column(BigInteger, primary_key=True, unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)

    # Основные данные объявления
    title = Column(String(255), nullable=False)
    price = Column(Integer, nullable=True) # Может быть None, если цена не указана
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    condition = Column(String(50), nullable=True)

    # Данные о продавце
    seller_name = Column(String(255), nullable=True)
    seller_rating = Column(Float, nullable=True)
    seller_reviews_count = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Ad(id={self.id}, title='{self.title[:30]}...')>"

# --- Блок для создания/обновления таблицы ---
if __name__ == "__main__":
    from src.db.session import engine

    print("Создаем/обновляем таблицы в базе данных...")
    # Base.metadata.drop_all(bind=engine) # Раскомментируй, если нужно полностью пересоздать
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы/обновлены.")