from typing import List, Dict
import random
from datetime import datetime, timedelta

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
    
    print(f"Сгенерировано {len(ads)} фейковых объявлений.")
    return ads