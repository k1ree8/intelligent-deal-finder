# src/parsers/avito_selenium_parser.py

import json
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Union

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from src.core.logger import log
from src.parsers.utils import parse_relative_date


def _parse_single_ad_block(ad_block_soup: BeautifulSoup) -> Union[Dict, None]:
    """
    Вспомогательная функция для парсинга HTML-блока одного объявления.
    Использует None для отсутствующих значений для удобства анализа.
    """
    base_url = "https://www.avito.ru"
    try:
        title_tag = ad_block_soup.find("a", {"data-marker": "item-title"})
        avito_id_raw = ad_block_soup.get("id")
        if not all([title_tag, avito_id_raw]):
            return None

        # --- ИЗВЛЕКАЕМ КАЖДОЕ ПОЛЕ БЕЗОПАСНО, ИСПОЛЬЗУЯ None КАК ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ ---
        
        price = None
        if price_tag := ad_block_soup.find("meta", {"itemprop": "price"}):
            try:
                price = int(price_tag["content"])
            except (ValueError, TypeError):
                pass

        published_at = datetime.now() # Запасное значение
        if date_tag := ad_block_soup.find("p", {"data-marker": "item-date"}):
            published_at = parse_relative_date(date_tag.text.strip()) or published_at
        
        location = None
        if location_tag := ad_block_soup.select_one('[class*="geo-root-"] span'):
            location = location_tag.text.strip()
        elif " в " in (full_title := title_tag.get("title", "")):
            location = full_title.split(" в ")[-1].strip()

        condition = None
        if params_tag := ad_block_soup.find("p", {"data-marker": "item-specific-params"}):
            params_text = params_tag.text.lower()
            if "новый" in params_text or "новая" in params_text:
                condition = "Новый"
            elif "/" in params_text:
                condition = "Б/у"

        description = None
        if description_tag := ad_block_soup.select_one('[class*="styles-module-root_bottom-"]'):
            description = description_tag.text.strip()

        seller_name = None
        seller_rating = None
        seller_reviews_count = None
        
        seller_link = ad_block_soup.select_one('a[href*="/profile"], a[href*="/user/"], a[href*="/brands/"]')
        if seller_link:
            if p_tag := seller_link.find("p"):
                seller_name = p_tag.text.strip()
            
            if rating_tag := seller_link.select_one('[data-marker="seller-rating/score"]'):
                try:
                    seller_rating = float(rating_tag.text.strip().replace(",", "."))
                except (ValueError, AttributeError):
                    pass # seller_rating останется None
            
            if reviews_tag := seller_link.select_one('[data-marker="seller-info/summary"]'):
                try:
                    seller_reviews_count = int("".join(filter(str.isdigit, reviews_tag.text.strip())))
                except (ValueError, AttributeError):
                    pass # seller_reviews_count останется None

        # --- СБОРКА СЛОВАРЯ ---
        ad_data = {
            "avito_id": int(avito_id_raw.lstrip("i")),
            "title": title_tag.text.strip(),
            "url": base_url + title_tag["href"],
            "price": price,
            "description": description,
            "location": location,
            "published_at": published_at,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_reviews_count": seller_reviews_count,
            "condition": condition,
        }
        return ad_data

    except Exception as e:
        log.warning(f"Пропущено объявление из-за НЕПРЕДВИДЕННОЙ общей ошибки: {e}")
        return None


def parse_avito_with_selenium(url: str, num_pages: int = 1) -> List[Dict]:
    """
    Парсит несколько страниц Avito с помощью Selenium, решая проблему Lazy Loading.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        log.info("Используем webdriver-manager для локального запуска.")
    except ImportError:
        log.info("webdriver-manager не найден. Используем системный chromedriver для Docker.")
        service = Service()

    driver = webdriver.Chrome(service=service, options=chrome_options)
    log.info("Selenium WebDriver запущен.")

    all_ads = []
    try:
        for page_num in range(1, num_pages + 1):
            base_url_for_pagination = url.split("&p=")[0]
            page_url = f"{base_url_for_pagination}&p={page_num}"

            log.info(f"Парсим страницу {page_num}: {page_url}")
            driver.get(page_url)
            time.sleep(random.uniform(3, 5))

            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            soup = BeautifulSoup(driver.page_source, "lxml")
            ads_blocks = soup.find_all("div", {"data-marker": "item"})
            log.info(f"На странице {page_num} найдено {len(ads_blocks)} объявлений.")

            for ad_block in ads_blocks:
                ad_data = _parse_single_ad_block(ad_block)
                if ad_data:
                    all_ads.append(ad_data)

            next_page_marker = f"pagination-button/page({page_num + 1})"
            next_page_button = soup.select_one(f'[data-marker="{next_page_marker}"]')

            if not next_page_button:
                log.info(
                    f"Кнопка для страницы {page_num + 1} не найдена. Завершаем пагинацию."
                )
                break

    finally:
        driver.quit()
        log.info("Selenium WebDriver закрыт.")

    log.info(f"Всего успешно распарсено {len(all_ads)} объявлений.")
    return all_ads