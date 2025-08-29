from sqlalchemy.orm import Session
from src.parsers.avito_parser import get_dummy_ads
from src.db.session import SessionLocal
from src.db.models import Ad

def process_ads():
    """
    The main handler function.
    Receives ads, checks for duplicates, and stores new ads in the database.
    """
    print("Начинаем процесс обработки объявлений...")
    new_ads_data = get_dummy_ads()

    with SessionLocal() as db:
        # --- Step 1: Extract the ID of all received ads ---
        new_avito_ids = {ad['avito_id'] for ad in new_ads_data}

        # --- Step 2: Find out which of these IDs are already in the database ---
        existing_ads = db.query(Ad.avito_id).filter(Ad.avito_id.in_(new_avito_ids)).all()
        existing_avito_ids = {ad_id for (ad_id,) in existing_ads}
        
        print(f"Найдено {len(existing_avito_ids)} уже существующих объявлений в БД.")

        # --- Step 3: Determine which ads are truly new ---
        ads_to_add = [
            ad_data for ad_data in new_ads_data 
            if ad_data['avito_id'] not in existing_avito_ids
        ]

        if not ads_to_add:
            print("Новых объявлений для добавления нет.")
            return

        print(f"Будет добавлено {len(ads_to_add)} новых объявлений.")

        # --- Step 4: Add only new ads ---
        try:
            for ad_data in ads_to_add:
                ad_model = Ad(**ad_data)
                db.add(ad_model)
            
            db.commit()
            print("Новые объявления успешно сохранены в базу данных.")
        except Exception as e:
            print(f"Произошла ошибка при сохранении: {e}")
            db.rollback()

if __name__ == "__main__":
    process_ads()