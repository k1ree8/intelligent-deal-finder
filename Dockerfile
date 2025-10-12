FROM apache/airflow:2.8.1

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl gnupg unzip jq wget

RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    google-chrome-stable

RUN CHROME_DRIVER_URL=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') && \
    wget -O /tmp/chromedriver.zip $CHROME_DRIVER_URL && \
    unzip -o /tmp/chromedriver.zip -d /usr/bin/ && \
    rm /tmp/chromedriver.zip

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN echo "APT::Install-Recommends \"false\";" > /etc/apt/apt.conf.d/99-no-install-recommends && \
    apt-get update && \
    apt-get install -y build-essential && \
    rm -f /etc/apt/apt.conf.d/99-no-install-recommends

USER airflow

COPY requirements.txt .

COPY ./src /opt/airflow/src
COPY ./models /opt/airflow/models

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres \
    "SQLAlchemy>=1.4.0,<2.0.0"