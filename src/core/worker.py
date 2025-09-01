import json
from typing import List, Dict
from sqlalchemy.orm import Session
from src.parsers.avito_parser import parse_avito_ads
from src.db.session import SessionLocal
from src.db.models import Ad

def process_ads() -> List[Dict]:
    """
    The main handler function.
    Receives ads, checks for duplicates, and stores new ads in the database.
    """
    print("Начинаем процесс обработки объявлений...")
    url_to_parse = "https://www.avito.ru/moskva/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?q=rtx+3080&s=104"
    new_ads_data = parse_avito_ads(url_to_parse)

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
            return []

        print(f"Будет добавлено {len(ads_to_add)} новых объявлений.")

        # --- Step 4: Add only new ads ---
        try:
            for ad_data in ads_to_add:
                ad_model = Ad(**ad_data)
                db.add(ad_model)
            
            db.commit()
            print("Новые объявления успешно сохранены в базу данных.")
            print(json.dumps(ads_to_add))
            return ads_to_add
        except Exception as e:
            print(f"Произошла ошибка при сохранении: {e}")
            db.rollback()
            print(json.dumps([]))
            return []

if __name__ == "__main__":
    process_ads()