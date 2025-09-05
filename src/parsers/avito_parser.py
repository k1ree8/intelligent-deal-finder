# src/parsers/avito_parser.py

import json
import random
import re
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
        sleep_time = random.uniform(7, 12)
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
            # --- Используем BeautifulSoup с проверками на None ---
            title_tag = ad_block.find("a", {"data-marker": "item-title"})
            price_tag = ad_block.find("meta", {"itemprop": "price"})
            avito_id_raw = ad_block.get("id")
            date_tag = ad_block.find("p", {"data-marker": "item-date"})

            if not all([title_tag, avito_id_raw, date_tag]):
                continue

            # --- ОБРАБОТКА ОСНОВНЫХ ДАННЫХ ---
            published_at = parse_relative_date(date_tag.text.strip()) or datetime.now()
            location = (
                title_tag.get("title", "").split(" в ")[-1].strip()
                if " в " in title_tag.get("title", "")
                else "Местоположение не указано"
            )

            description = "Описание отсутствует"
            description_tag = ad_block.select_one(
                '[class*="styles-module-root_bottom-"]'
            )
            if description_tag:
                description = description_tag.text.strip()

            condition = "Не указано"
            params_tag = ad_block.find("p", {"data-marker": "item-specific-params"})
            if params_tag:
                params_text = params_tag.text.lower()
                if "б/у" in params_text:
                    condition = "Б/у"
                elif "новый" in params_text or "новая" in params_text:
                    condition = "Новый"

            # --- ОБРАБОТКА ДАННЫХ О ПРОДАВЦЕ (самый надежный способ) ---
            seller_name = "Имя не указано"
            seller_rating = 0.0
            seller_reviews_count = 0

            seller_rating_block = ad_block.find(attrs={"data-marker": "seller-rating"})
            if seller_rating_block:
                seller_link = seller_rating_block.find_previous(
                    "a", href=re.compile(r"/profile/|/user/|/brands/")
                )
                if seller_link and seller_link.find("p"):
                    seller_name = seller_link.find("p").text.strip()

                rating_tag = seller_rating_block.select_one(
                    '[data-marker="seller-rating/score"]'
                )
                if rating_tag:
                    try:
                        seller_rating = float(rating_tag.text.strip().replace(",", "."))
                    except (ValueError, AttributeError):
                        pass

                reviews_tag = seller_rating_block.select_one(
                    '[data-marker="seller-info/summary"]'
                )
                if reviews_tag:
                    try:
                        seller_reviews_count = int(
                            "".join(filter(str.isdigit, reviews_tag.text.strip()))
                        )
                    except (ValueError, AttributeError):
                        pass

            # --- СБОРКА СЛОВАРЯ ---
            ad_data = {
                "avito_id": int(avito_id_raw.lstrip("i")),
                "title": title_tag.text.strip(),
                "url": base_url + title_tag["href"],
                "price": int(price_tag["content"]) if price_tag else None,
                "description": description,
                "location": location,
                "published_at": published_at,
                "seller_name": seller_name,
                "seller_rating": seller_rating,
                "seller_reviews_count": seller_reviews_count,
                "condition": condition,
            }
            parsed_ads.append(ad_data)

        except Exception as e:
            log.warning(f"Пропущено объявление из-за общей ошибки: {e}")
            continue

    log.info(f"Успешно распарсено {len(parsed_ads)} объявлений.")
    return parsed_ads


# --- ТЕСТОВЫЙ БЛОК ---
if __name__ == "__main__":
    test_url = "https://www.avito.ru/all/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc?context=H4sIAAAAAAAA_wEmANn_YToxOntzOjE6InkiO3M6MTY6IkFRcHJJTThNMHJNVmo2WnkiO31OhhXxJgAAAA&d=1&p=1&s=104"

    results = parse_avito_ads(test_url)

    if results:
        print("\n--- Пример результата (первое объявление) ---")

        first_ad = results[0]
        if isinstance(first_ad.get("published_at"), datetime):
            first_ad["published_at"] = first_ad["published_at"].isoformat()

        print(json.dumps(first_ad, indent=2, ensure_ascii=False))
