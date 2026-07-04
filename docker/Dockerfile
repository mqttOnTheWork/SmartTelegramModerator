# Многоступенчатая сборка: сначала ставим зависимости, потом кладём код.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости для сборки некоторых колёс (bcrypt/asyncpg).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY dashboard ./dashboard

# Непривилегированный пользователь — не запускаем контейнер от root.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# По умолчанию поднимаем API + дашборд. Бота можно запускать отдельной командой:
#   python -m app.main
CMD ["uvicorn", "app.api.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000"]
