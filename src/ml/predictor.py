# src/ml/predictor.py

import joblib
import json
import pandas as pd
from typing import List, Dict
from src.core.config import settings

# --- Константы ---
# Пути внутри Docker-контейнера Airflow
MODEL_PATH = "/opt/airflow/models/price_predictor_model.pkl"
COLUMNS_PATH = "/opt/airflow/models/model_columns.json"

# --- Загружаем модель и колонки один раз при старте ---
try:
    model = joblib.load(MODEL_PATH)
    with open(COLUMNS_PATH, 'r') as f:
        model_columns = json.load(f)
except FileNotFoundError:
    model = None
    model_columns = None
    print("Warning: Model files not found. Predictor will not work.")

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Применяет ту же самую логику создания признаков, что и в ноутбуке.
    """
    df['description_lower'] = df['description'].str.lower().fillna('')
    
    df['has_defect'] = df['description_lower'].str.contains('дефект|разбит|царапин|трещин|менялся|ремонт', na=False).astype(int)
    df['is_ideal'] = df['description_lower'].str.contains('идеал|отличн|как нов', na=False).astype(int)
    df['has_box'] = df['description_lower'].str.contains('коробк', na=False).astype(int)
    df['not_opened'] = df['description_lower'].str.contains('не вскрывался|не ремонтировался', na=False).astype(int)
    df['has_warranty'] = df['description_lower'].str.contains('гаранти', na=False).astype(int)
    
    return df

def predict_and_filter(new_ads: List[Dict]) -> List[Dict]:
    """
    Принимает список новых объявлений, предсказывает цену и фильтрует выгодные.
    """
    if not new_ads or model is None:
        return []
    
    # <-- ПОЛУЧАЕМ ПОРОГ ИЗ КОНФИГА -->
    profit_threshold = settings.get_profit_threshold()

    # 1. Превращаем в DataFrame
    df = pd.DataFrame(new_ads)

    # 2. Применяем Feature Engineering
    df = feature_engineering(df)

    # 3. Применяем one-hot encoding
    # Важно: 'model' и 'memory' должны быть в данных
    df_encoded = pd.get_dummies(df, columns=['model', 'memory'])
    
    # 4. Приводим колонки к тому же виду, что и при обучении
    # `reindex` добавит недостающие колонки (если в новых данных их нет) и заполнит их 0
    df_aligned = df_encoded.reindex(columns=model_columns, fill_value=0)

    # 5. Делаем предсказание
    predictions = model.predict(df_aligned)
    df['predicted_price'] = predictions
    df['profit'] = df['predicted_price'] - df['price']

    # 6. Фильтруем только выгодные предложения
    profitable_ads_df = df[df['profit'] >= profit_threshold]

    # 7. Возвращаем результат в виде списка словарей
    return profitable_ads_df.to_dict('records')