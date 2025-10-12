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


def parse_avito_ads(url: str, save_html: bool = False) -> List[Dict]:
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

    if save_html:
        filename = f"avito_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        log.info(f"HTML страницы сохранен в файл: {filename}")

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
            title_tag = ad_block.find("a", {"data-marker": "item-title"})
            price_tag = ad_block.find("meta", {"itemprop": "price"})
            avito_id_raw = ad_block.get("id")
            date_tag = ad_block.find("p", {"data-marker": "item-date"})

            if not all([title_tag, avito_id_raw, date_tag]):
                continue

            published_at = parse_relative_date(date_tag.text.strip()) or datetime.now()

            location = "Местоположение не указано"
            location_tag = ad_block.select_one('[class*="geo-root-"] span')
            if location_tag:
                location = location_tag.text.strip()
            else:
                full_title = title_tag.get("title", "")
                if " в " in full_title:
                    location = full_title.split(" в ")[-1].strip()

            condition = "Не указано"
            if params_tag := ad_block.find(
                "p", {"data-marker": "item-specific-params"}
            ):
                params_text = params_tag.text.lower()
                if "новый" in params_text or "новая" in params_text:
                    condition = "Новый"
                elif "/" in params_text:
                    condition = "Б/у"

            description = "Описание отсутствует"
            if description_tag := ad_block.select_one(
                '[class*="styles-module-root_bottom-"]'
            ):
                description = description_tag.text.strip()

            seller_name = "Имя не указано"
            seller_rating = 0.0
            seller_reviews_count = 0

            seller_link = ad_block.select_one(
                'a[href*="/profile"], a[href*="/user/"], a[href*="/brands/"]'
            )
            if seller_link and (p_tag := seller_link.find("p")):
                seller_name = p_tag.text.strip()

            if rating_tag := ad_block.select_one('[data-marker="seller-rating/score"]'):
                try:
                    seller_rating = float(rating_tag.text.strip().replace(",", "."))
                except (ValueError, AttributeError):
                    pass

            if reviews_tag := ad_block.select_one(
                '[data-marker="seller-info/summary"]'
            ):
                try:
                    seller_reviews_count = int(
                        "".join(filter(str.isdigit, reviews_tag.text.strip()))
                    )
                except (ValueError, AttributeError):
                    pass

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