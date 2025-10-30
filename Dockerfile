# Базовый образ с Python
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей (для psycopg2 и т.д.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта
COPY . .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Экспонируем порт Streamlit
EXPOSE 8501

# Указываем Streamlit, что он должен слушать все интерфейсы
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

# Загружаем переменные окружения из .env
# (необязательно, можно использовать docker-compose)
# ENV API_KEY=...
# ENV BASE_URL=...
# ENV CHAT_MODEL=gpt-4o-mini

# Команда запуска
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
