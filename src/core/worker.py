import json
from typing import List, Dict
from sqlalchemy.orm import Session
from src.parsers.avito_parser import parse_avito_ads
from src.db.session import SessionLocal
from src.db.models import Ad
from src.parsers.avito_parser import parse_avito_ads
from src.core.config import settings
from src.core.logger import log
from datetime import datetime

def process_ads(use_sort: bool = False) -> List[Dict]:
    """
    Основная функция-обработчик.
    
    Args:
        use_sort: Использовать ли сортировку по дате (для backfill).
    """
    log.info("Начинаем процесс обработки объявлений...")
    url_to_parse = settings.get_parser_url(use_sort=use_sort)
    log.info(f"Парсим URL: {url_to_parse}")
    new_ads_data = parse_avito_ads(url_to_parse)

    with SessionLocal() as db:
        # --- Step 1: Extract the ID of all received ads ---
        new_avito_ids = {ad['avito_id'] for ad in new_ads_data}

        # --- Step 2: Find out which of these IDs are already in the database ---
        existing_ads = db.query(Ad.avito_id).filter(Ad.avito_id.in_(new_avito_ids)).all()
        existing_avito_ids = {ad_id for (ad_id,) in existing_ads}
        
        log.info(f"Найдено {len(existing_avito_ids)} уже существующих объявлений в БД.")

        # --- Step 3: Determine which ads are truly new ---
        ads_to_add = [
            ad_data for ad_data in new_ads_data 
            if ad_data['avito_id'] not in existing_avito_ids
        ]

        if not ads_to_add:
            log.info("Новых объявлений для добавления нет.")
            return []

        log.info(f"Будет добавлено {len(ads_to_add)} новых объявлений.")

        # --- Step 4: Add only new ads ---
        try:
            for ad_data in ads_to_add:
                ad_model = Ad(**ad_data)
                db.add(ad_model)
            
            db.commit()
            log.info("Новые объявления успешно сохранены в базу данных.")
            def json_converter(o):
                if isinstance(o, datetime):
                    return o.isoformat()
            print(json.dumps(ads_to_add, default=json_converter))
            return ads_to_add
        except Exception as e:
            log.error(f"Произошла ошибка при сохранении: {e}", exc_info=True)
            db.rollback()
            print(json.dumps([]))
            return []

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sort', 
        action='store_true', 
        help='Использовать сортировку по дате для начальной загрузки.'
    )
    args = parser.parse_args()
    
    process_ads(use_sort=args.sort)