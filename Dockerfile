# Dockerfile
FROM apache/airflow:2.8.1

USER root
RUN echo "APT::Install-Recommends \"false\";" > /etc/apt/apt.conf.d/99-no-install-recommends && \
    apt-get update && \
    apt-get install -y build-essential && \
    rm -f /etc/apt/apt.conf.d/99-no-install-recommends
USER airflow

# Копируем наши зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
# Устанавливаем наши зависимости
RUN pip install --no-cache-dir -r requirements.txt
# Устанавливаем зависимости Airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres \
    "SQLAlchemy>=1.4.0,<2.0.0"