from __future__ import annotations

import json
from typing import Any

import httpx

SYSTEM_PROMPT = """
Ты помощник, который преобразует русскоязычные вопросы про метрики видео в строгий JSON.
Нужно вернуть ТОЛЬКО JSON без текста вокруг.

Доступны таблицы PostgreSQL:
1) videos (итоговая статистика по ролику)
- id (text)
- creator_id (text)
- video_created_at (timestamptz) — время публикации
- views_count, likes_count, comments_count, reports_count (bigint) — финальные значения
- created_at, updated_at (timestamptz)

2) video_snapshots (почасовые замеры)
- id (text)
- video_id (text) — ссылка на videos.id
- views_count, likes_count, comments_count, reports_count (bigint) — текущие значения на момент замера
- delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count (bigint) — приращения с прошлого замера
- created_at (timestamptz) — время замера
- updated_at (timestamptz)

Формат JSON (QuerySpec):
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

Правила:
- Итоговые значения/"за всё время" => source="videos".
- Прирост/"выросли"/"новые просмотры" => source="video_snapshots" и использовать delta_*.
- "Сколько видео" => aggregation="count".
- "Сколько разных видео" => aggregation="count_distinct" и field="video_id".
- Одна дата => date_from = date_to.
- Диапазоны дат включительные, указывай только даты (YYYY-MM-DD).
- Если фильтр по creator_id, использовать filters.
- Если речь о просмотрах/лайках/комментариях/жалобах без слова "прирост" — это итоговые значения (videos.*).

Примеры:
Вопрос: "Сколько всего видео есть в системе?"
Ответ:
{"source":"videos","aggregation":"count","field":null,"date_field":null,"date_from":null,"date_to":null,"filters":[]}

Вопрос: "Сколько видео набрало больше 100000 просмотров за всё время?"
Ответ:
{"source":"videos","aggregation":"count","field":null,"date_field":null,"date_from":null,"date_to":null,"filters":[{"field":"views_count","op":">","value":100000}]}

Вопрос: "Сколько видео у креатора с id abc вышло с 1 ноября 2025 по 5 ноября 2025?"
Ответ:
{"source":"videos","aggregation":"count","field":null,"date_field":"video_created_at","date_from":"2025-11-01","date_to":"2025-11-05","filters":[{"field":"creator_id","op":"=","value":"abc"}]}

Вопрос: "Сколько разных видео получали новые просмотры 27 ноября 2025?"
Ответ:
{"source":"video_snapshots","aggregation":"count_distinct","field":"video_id","date_field":"created_at","date_from":"2025-11-27","date_to":"2025-11-27","filters":[{"field":"delta_views_count","op":">","value":0}]}
""".strip()


async def gemini_query(api_key: str, model: str, user_text: str) -> dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nВопрос пользователя: {user_text}"}]}
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, params={"key": api_key}, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Gemini returns: candidates[0].content.parts[0].text
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # fallback: try to extract JSON substring
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
