# Используем легковесный базовый образ с Python
FROM python:3.11-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копирование приложения и зависимостей
COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY entrypoint.sh /entrypoint.sh

# Разрешения для запуска entrypoint
RUN chmod +x /entrypoint.sh

# Установка зависимостей Python в виртуальном окружении
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Установка рабочей директории
WORKDIR /app

# Открытие порта для Dashboard
EXPOSE 80

# HEALTHCHECK (проверяем, что приложение отвечает на HTTP-запросы)
HEALTHCHECK CMD curl --fail http://localhost:80/ || exit 1

# Запуск через entrypoint
ENTRYPOINT ["/usr/bin/dumb-init", "/entrypoint.sh"]
