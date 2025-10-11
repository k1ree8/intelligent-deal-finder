# Используем официальный образ Airflow версии 2.8.1
FROM apache/airflow:2.8.1

# Переключаемся на пользователя root для установки системных пакетов
USER root

# Шаг 1: Устанавливаем базовые утилиты, необходимые для последующих шагов
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl gnupg unzip jq wget

# Шаг 2: Добавляем ключ и репозиторий Google Chrome для его установки
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Шаг 3: Устанавливаем Google Chrome
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    google-chrome-stable

# Шаг 4: Скачиваем и устанавливаем chromedriver, соответствующий стабильной версии Chrome
# Это гарантирует, что драйвер всегда будет совместим с браузером
RUN CHROME_DRIVER_URL=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') && \
    wget -O /tmp/chromedriver.zip $CHROME_DRIVER_URL && \
    unzip -o /tmp/chromedriver.zip -d /usr/bin/ && \
    rm /tmp/chromedriver.zip

# Шаг 5: Устанавливаем зависимости для работы Chrome в headless-режиме и очищаем кэш APT
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN echo "APT::Install-Recommends \"false\";" > /etc/apt/apt.conf.d/99-no-install-recommends && \
    apt-get update && \
    apt-get install -y build-essential && \
    rm -f /etc/apt/apt.conf.d/99-no-install-recommends

# Возвращаемся к пользователю airflow для выполнения операций, не требующих прав root
USER airflow

# Копируем файл с Python-зависимостями в рабочую директорию
COPY requirements.txt .

# -----------------------------------------------------------------------------
# --> ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ <--
# Копируем все необходимые файлы нашего приложения в образ
# Это делает образ самодостаточным
COPY ./src /opt/airflow/src
COPY ./models /opt/airflow/models
# -----------------------------------------------------------------------------

# Обновляем pip
RUN pip install --no-cache-dir --upgrade pip

# Устанавливаем Python-зависимости из нашего проекта
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем дополнительные провайдеры и зависимости для Airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres \
    "SQLAlchemy>=1.4.0,<2.0.0"