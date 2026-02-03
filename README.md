# Telegram‑бот для аналитики видео

Асинхронный Telegram‑бот (aiogram v3), который отвечает одним числом на русскоязычные запросы, используя PostgreSQL и Gemini API для преобразования NL → QuerySpec → SQL.

## Быстрый старт (Docker)
1. Скопируйте `.env.example` в `.env` и заполните значения:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
2. Положите `videos.json` в корень проекта (файл **не** коммитится).
3. Запустите PostgreSQL:
   ```bash
   docker compose up -d db
   ```
4. Примените миграцию:
   ```bash
   cat migrations/001_init.sql | docker exec -i $(docker compose ps -q db) psql -U postgres -d app
   ```
5. Загрузите данные:
   ```bash
   docker compose run --rm bot python scripts/load_json.py
   ```
6. Запустите бота:
   ```bash
   docker compose up bot
   ```

## Локальный запуск (без Docker)
1. Создайте БД и примените `migrations/001_init.sql`.
2. Установите зависимости:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Укажите ENV: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`.
4. Загрузите данные:
   ```bash
   python scripts/load_json.py
   ```
5. Запустите бота:
   ```bash
   python -m app.bot
   ```

## Архитектура
1. Пользователь отправляет вопрос.
2. `Gemini API` возвращает **строгий JSON** (QuerySpec).
3. JSON валидируется (Pydantic) и преобразуется в параметризованный SQL.
4. Бот возвращает одно число.

## QuerySpec (формат)
```json
{
  "source": "videos" | "video_snapshots",
  "aggregation": "count" | "count_distinct" | "sum",
  "field": "id" | "video_id" | "creator_id" | "video_created_at" | "views_count" | "likes_count" | "comments_count" | "reports_count" | "delta_views_count" | "delta_likes_count" | "delta_comments_count" | "delta_reports_count" | "created_at",
  "date_field": "video_created_at" | "created_at",
  "date_from": "YYYY-MM-DD",
  "date_to": "YYYY-MM-DD",
  "filters": [
    {"field": "creator_id" | "video_id" | "views_count" | "likes_count" | "comments_count" | "reports_count" | "delta_views_count" | "delta_likes_count" | "delta_comments_count" | "delta_reports_count", "op": "="|">"|">="|"<"|"<=", "value": "string|number"}
  ]
}
```

## Пример запросов
- «Сколько всего видео есть в системе?»
- «Сколько видео у креатора с id ... вышло с 1 ноября 2025 по 5 ноября 2025?»
- «Сколько видео набрало больше 100 000 просмотров за всё время?»
- «На сколько просмотров в сумме выросли все видео 28 ноября 2025?»
- «Сколько разных видео получали новые просмотры 27 ноября 2025?»

## Примечания
- Даты интерпретируются как UTC.
- `videos.json` должен лежать в корне и не коммитится.

## Тесты (опционально)
```bash
pip install -r requirements-dev.txt
pytest
```
