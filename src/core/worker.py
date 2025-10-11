# src/core/worker.py

import argparse
import json
from datetime import datetime
from typing import Dict, List
import pandas as pd
import re # Импортируем для использования в фильтре

from src.core.config import settings
from src.core.logger import log
from src.db.models import Ad
from src.db.session import SessionLocal
from src.parsers.avito_selenium_parser import parse_avito_with_selenium


def process_ads(num_pages: int = 1) -> List[Dict]:
    """
    Основная функция-обработчик.
    Запускает парсер, фильтрует объявления СТРОГО по формату "Модель, Память",
    обогащает данные, проверяет наличие в БД и сохраняет новые.
    """
    log.info("Начинаем процесс обработки объявлений с помощью Selenium...")
    url_to_parse = settings.get_parser_url()
    log.info(f"Парсим URL из конфига: {url_to_parse}")
    new_ads_data = parse_avito_with_selenium(url_to_parse, num_pages=num_pages)
    if not new_ads_data:
        log.info("Парсер не вернул новых данных. Завершение работы.")
        print(json.dumps([]))
        return []
    
    log.info(f"Получено {len(new_ads_data)} записей от парсера. Начинаем дедупликацию...")
    unique_ads_dict = {ad["avito_id"]: ad for ad in new_ads_data}
    unique_ads_list = list(unique_ads_dict.values())
    log.info(f"После дедупликации осталось {len(unique_ads_list)} уникальных записей.")
    
    # -----------------------------------------------------------------------------
    # --> СТРОГИЙ БЛОК ФИЛЬТРАЦИИ И ОБОГАЩЕНИЯ <--
    if not unique_ads_list:
        print(json.dumps([]))
        return []
        
    df = pd.DataFrame(unique_ads_list)
    original_count = len(df)

    # 1. Определяем "идеальный" шаблон:
    # ^iPhone ... , ... ГБ/ТБ$  (от начала и до конца строки)
    perfect_title_pattern = r'^iPhone[\w\s]+,\s\d+\s(?:ГБ|ТБ)$'

    # 2. Фильтруем DataFrame, оставляя только строки, полностью соответствующие шаблону
    df = df[df['title'].str.match(perfect_title_pattern, na=False)].copy()
    log.info(f"Отфильтровано по ИДЕАЛЬНОМУ формату заголовка. Осталось {len(df)} из {original_count} объявлений.")

    # 3. Разделяем 'title' на 'model' и 'memory' (теперь это на 100% безопасно)
    if not df.empty:
        split_data = df['title'].str.split(', ', n=1, expand=True)
        df['model'] = split_data[0].str.strip()
        df['memory'] = split_data[1].str.strip()
        log.info("Столбец 'title' успешно разделен на 'model' и 'memory'.")
    else:
        # Если после фильтрации ничего не осталось, создаем пустые колонки
        df['model'] = pd.Series(dtype='str')
        df['memory'] = pd.Series(dtype='str')

    unique_ads_list = df.to_dict('records')
    # -----------------------------------------------------------------------------

    ads_to_add_data = []
    with SessionLocal() as db:
        new_avito_ids = {ad["avito_id"] for ad in unique_ads_list}
        if not new_avito_ids:
            log.info("После строгой фильтрации не осталось объявлений для обработки.")
            print(json.dumps([]))
            return []
        existing_ads_query = db.query(Ad.avito_id).filter(Ad.avito_id.in_(new_avito_ids))
        existing_avito_ids = {ad_id for (ad_id,) in existing_ads_query.all()}
        log.info(f"Найдено {len(existing_avito_ids)} уже существующих объявлений в БД.")
        ads_to_add_data = [ad_data for ad_data in unique_ads_list if ad_data["avito_id"] not in existing_avito_ids]
        if not ads_to_add_data:
            log.info("Новых объявлений для добавления нет.")
            print(json.dumps([]))
            return []
        log.info(f"Будет добавлено {len(ads_to_add_data)} новых объявлений.")
        try:
            for ad_data in ads_to_add_data:
                ad_model = Ad(**ad_data)
                db.add(ad_model)
            db.commit()
            log.info("Новые объявления успешно сохранены в базу данных.")
            def json_converter(o):
                if isinstance(o, datetime):
                    return o.isoformat()
            print(json.dumps(ads_to_add_data, default=json_converter))
            return ads_to_add_data
        except Exception as e:
            log.error(f"Произошла ошибка при сохранении: {e}", exc_info=True)
            db.rollback()
            print(json.dumps([]))
            return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск воркера для сбора объявлений.")
    parser.add_argument(
        "--pages", type=int, default=1, help="Количество страниц для парсинга."
    )
    args = parser.parse_args()
    process_ads(num_pages=args.pages)