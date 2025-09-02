from typing import List, Dict
import random
from datetime import datetime, timedelta
import time
from src.core.logger import log

import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
]

def get_dummy_ads() -> List[Dict]:
    """Generates a list of dictionaries that mimic the ad data obtained from Avito."""
    ads = []
    base_avito_id = random.randint(3_000_000_000, 4_000_000_000)

    for i in range(random.randint(5, 15)):
        price = random.randint(15_000, 100_000)

        ad = {
            "avito_id": base_avito_id + i,
            "url": f"https://www.avito.ru/moskva/tovary_dlya_kompyutera/videokarta_rtx_3080_{base_avito_id + i}",
            "title": f"Видеокарта RTX 3080 (Модель #{i+1})",
            "description": "Отличное состояние, использовалась для игр. Не майнилась!",
            "category": "Товары для компьютера",
            "location": random.choice(["Москва, м. Арбатская", "Санкт-Петербург, м. Невский проспект", "Екатеринбург, Площадь 1905 года"]),
            "price": price,
            "published_at": datetime.now() - timedelta(minutes=random.randint(1, 60*24)),
            "seller_name": f"Продавец_{random.randint(100, 999)}",
            "delivery_available": random.choice([True, False]),
            "parameters": {
                "condition": random.choice(["Новое", "Б/у"]),
                "brand": random.choice(["Gigabyte", "MSI", "Palit"])
            }
        }
        ads.append(ad)
    
    log.info(f"Сгенерировано {len(ads)} фейковых объявлений.")
    return ads

def parse_avito_ads(url: str) -> List[Dict]:
    """
    Парсит страницу Avito и возвращает список словарей с данными об объявлениях.
    """
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    try:
        sleep_time = random.uniform(1, 4)
        log.info(f"Делаем паузу на {sleep_time:.2f} секунд...")
        time.sleep(sleep_time)

        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        log.error(f"Ошибка при запросе к {url}: {e}")
        return [] # Возвращаем пустой список в случае ошибки

    soup = BeautifulSoup(response.text, 'lxml')
    ads_blocks = soup.find_all('div', {'data-marker': 'item'})
    
    if not ads_blocks:
        log.info("Не найдено ни одного блока с объявлениями.")
        return []

    log.info(f"Найдено {len(ads_blocks)} объявлений на странице.")
    
    # --- НОВЫЙ КОД: ЦИКЛ И ФОРМАТИРОВАНИЕ ---
    parsed_ads = []
    base_url = "https://www.avito.ru"

    for ad_block in ads_blocks:
        try:
            # Извлекаем заголовок и ссылку
            title_tag = ad_block.find('a', {'data-marker': 'item-title'})
            # Извлекаем цену
            price_tag = ad_block.find('meta', {'itemprop': 'price'})
            # Извлекаем ID
            avito_id_raw = ad_block.get('id')
            
            # --- Пропускаем рекламные блоки или блоки без данных ---
            if not all([title_tag, price_tag, avito_id_raw]):
                continue

            # --- Собираем данные в словарь ---
            ad_data = {
                "avito_id": int(avito_id_raw.lstrip('i')),
                "title": title_tag.text.strip(),
                "url": base_url + title_tag['href'],
                "price": int(price_tag['content']),
                # --- Добавляем заглушки для полей, которые мы пока не парсим ---
                "published_at": datetime.now(), # Заглушка
                "description": "Описание будет здесь...", # Заглушка
                "location": "Город будет здесь...", # Заглушка
            }
            parsed_ads.append(ad_data)

        except (AttributeError, TypeError, ValueError) as e:
            # Ловим возможные ошибки, если структура блока отличается
            print(f"Пропущено объявление из-за ошибки парсинга: {e}")
            continue

    log.info(f"Успешно распарсено {len(parsed_ads)} объявлений.")
    return parsed_ads


if __name__ == '__main__':
    test_url = "https://www.avito.ru/moskva/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?q=rtx+3080&s=104"
    
    results = parse_avito_ads(test_url)
    
    if results:
        log.info("\n--- Пример результата (первое объявление) ---")
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Преобразуем datetime в строку ПЕРЕД печатью
        first_ad = results[0]
        first_ad['published_at'] = first_ad['published_at'].isoformat()
        
        import json
        log.info(json.dumps(first_ad, indent=2, ensure_ascii=False))