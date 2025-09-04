# src/parsers/avito_parser.py

import json
import random
import time
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from src.core.logger import log
from src.parsers.utils import parse_relative_date

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
]


def parse_avito_ads(url: str) -> List[Dict]:
    """
    Парсит страницу Avito и возвращает список словарей с данными об объявлениях.
    """
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    try:
        sleep_time = random.uniform(2, 5)  # Немного увеличим паузу для надежности
        log.info(f"Делаем паузу на {sleep_time:.2f} секунд...")
        time.sleep(sleep_time)

        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        log.error(f"Ошибка при запросе к {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    ads_blocks = soup.find_all("div", {"data-marker": "item"})

    if not ads_blocks:
        log.warning("Не найдено ни одного блока с объявлениями.")
        return []

    log.info(f"Найдено {len(ads_blocks)} объявлений на странице.")

    parsed_ads = []
    base_url = "https://www.avito.ru"

    for ad_block in ads_blocks:
        try:
            # --- СНАЧАЛА ИЗВЛЕКАЕМ ВСЕ НУЖНЫЕ ТЕГИ ---
            title_tag = ad_block.find("a", {"data-marker": "item-title"})
            price_tag = ad_block.find("meta", {"itemprop": "price"})
            avito_id_raw = ad_block.get("id")
            date_tag = ad_block.find("p", {"data-marker": "item-date"})
            description_tag = ad_block.select_one(
                '[class*="styles-module-root_bottom-"]'
            )
            location_tag = ad_block.select_one(
                '[class*="geo-georeferences-"]'
            )  # Более надежный селектор для местоположения

            # --- ПРОВЕРЯЕМ КРИТИЧЕСКИ ВАЖНЫЕ ДАННЫЕ ---
            if not all([title_tag, avito_id_raw, date_tag]):
                continue  # Пропускаем, если нет заголовка, ID или даты

            # --- ТЕПЕРЬ ОБРАБАТЫВАЕМ ДАННЫЕ ---
            published_at_text = date_tag.text.strip()
            published_at = parse_relative_date(published_at_text) or datetime.now()

            # --- СБОРКА СЛОВАРЯ ---
            ad_data = {
                "avito_id": int(avito_id_raw.lstrip("i")),
                "title": title_tag.text.strip(),
                "url": base_url + title_tag["href"],
                "price": int(price_tag["content"]) if price_tag else None,
                "description": (
                    description_tag.text.strip()
                    if description_tag
                    else "Описание отсутствует"
                ),
                "location": (
                    location_tag.text.strip().split("\n")[0]
                    if location_tag
                    else "Местоположение не указано"
                ),
                "published_at": published_at,
            }
            parsed_ads.append(ad_data)

        except (AttributeError, TypeError, ValueError) as e:
            log.warning(f"Пропущено объявление из-за ошибки парсинга: {e}")
            continue

    log.info(f"Успешно распарсено {len(parsed_ads)} объявлений.")
    return parsed_ads


# --- ОБНОВИМ ТЕСТОВЫЙ БЛОК ---
if __name__ == "__main__":
    # URL для теста (поиск iPhone по всей России с доставкой, отсортированный по дате)
    test_url = "https://www.avito.ru/all/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc?d=1&s=104"

    results = parse_avito_ads(test_url)

    if results:
        print("\n--- Пример результата (первое объявление) ---")

        first_ad = results[0]
        # Преобразуем datetime в строку ПЕРЕД печатью
        if isinstance(first_ad.get("published_at"), datetime):
            first_ad["published_at"] = first_ad["published_at"].isoformat()

        print(json.dumps(first_ad, indent=2, ensure_ascii=False))
