import asyncio
import json
import os
from typing import Any

import asyncpg


def build_video_row(video: dict[str, Any]) -> tuple:
    return (
        video["id"],
        video["creator_id"],
        video["video_created_at"],
        video["views_count"],
        video["likes_count"],
        video["comments_count"],
        video["reports_count"],
        video["created_at"],
        video["updated_at"],
    )


def build_snapshot_row(snapshot: dict[str, Any]) -> tuple:
    return (
        snapshot["id"],
        snapshot["video_id"],
        snapshot["views_count"],
        snapshot["likes_count"],
        snapshot["comments_count"],
        snapshot["reports_count"],
        snapshot["delta_views_count"],
        snapshot["delta_likes_count"],
        snapshot["delta_comments_count"],
        snapshot["delta_reports_count"],
        snapshot["created_at"],
        snapshot["updated_at"],
    )


async def main() -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is required")

    json_path = os.getenv("VIDEO_JSON_PATH", "videos.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"{json_path} not found")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    video_rows = [build_video_row(v) for v in videos]
    snapshot_rows = [build_snapshot_row(s) for v in videos for s in v.get("snapshots", [])]

    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO videos (
                    id, creator_id, video_created_at, views_count, likes_count, comments_count,
                    reports_count, created_at, updated_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                ON CONFLICT (id) DO NOTHING
                """,
                video_rows,
            )
            await conn.executemany(
                """
                INSERT INTO video_snapshots (
                    id, video_id, views_count, likes_count, comments_count, reports_count,
                    delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count,
                    created_at, updated_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (id) DO NOTHING
                """,
                snapshot_rows,
            )

    await pool.close()
    print(f"Loaded {len(video_rows)} videos and {len(snapshot_rows)} snapshots")


if __name__ == "__main__":
    asyncio.run(main())
