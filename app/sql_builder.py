from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

from app.query_spec import Filter, QuerySpec


@dataclass
class SQLQuery:
    sql: str
    params: list


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_range(date_from: str, date_to: str) -> tuple[datetime, datetime]:
    start_date = _parse_date(date_from)
    end_date = _parse_date(date_to)
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    start_dt = datetime.combine(start_date, time(0, 0), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date + timedelta(days=1), time(0, 0), tzinfo=timezone.utc)
    return start_dt, end_dt


def build_sql(spec: QuerySpec) -> SQLQuery:
    params: list = []
    where: list[str] = []

    use_snapshots = spec.source == "video_snapshots"
    base_alias = "s" if use_snapshots else "v"
    joins: list[str] = []

    need_videos_join = False
    if use_snapshots:
        if spec.date_field == "video_created_at":
            need_videos_join = True
        for f in spec.filters:
            if f.field in {"creator_id", "video_created_at"}:
                need_videos_join = True

    if need_videos_join:
        joins.append("JOIN videos v ON s.video_id = v.id")

    # SELECT
    if spec.aggregation == "count":
        select_expr = "count(*)"
    elif spec.aggregation == "count_distinct":
        field = _resolve_field(spec.field, base_alias, need_videos_join)
        select_expr = f"count(distinct {field})"
    else:  # sum
        if spec.field in {"id", "video_id", "creator_id", "video_created_at", "created_at"}:
            raise ValueError("Sum is only allowed for numeric metric fields")
        field = _resolve_field(spec.field, base_alias, need_videos_join)
        select_expr = f"sum({field})"

    # Date filters
    if spec.date_field and spec.date_from and spec.date_to:
        column = _resolve_field(spec.date_field, base_alias, need_videos_join)
        start_dt, end_dt = _date_range(spec.date_from, spec.date_to)
        params.extend([start_dt, end_dt])
        where.append(f"{column} >= ${len(params)-1} AND {column} < ${len(params)}")

    # Other filters
    for f in spec.filters:
        column = _resolve_field(f.field, base_alias, need_videos_join)
        params.append(f.value)
        where.append(f"{column} {f.op} ${len(params)}")

    base_table = "video_snapshots s" if use_snapshots else "videos v"
    sql = f"SELECT {select_expr} FROM {base_table}"
    if joins:
        sql += " " + " ".join(joins)
    if where:
        sql += " WHERE " + " AND ".join(where)

    return SQLQuery(sql=sql, params=params)


def _resolve_field(field: str | None, base_alias: str, has_videos_join: bool) -> str:
    if field is None:
        raise ValueError("Field is required for this aggregation")

    # videos-only fields
    if field in {"creator_id", "video_created_at"}:
        if base_alias == "v":
            return f"v.{field}"
        if has_videos_join:
            return f"v.{field}"
        raise ValueError(f"Field {field} requires join with videos")

    if field == "video_id" and base_alias == "v":
        raise ValueError("Field video_id is not available in videos")

    if field in {"id", "video_id", "views_count", "likes_count", "comments_count", "reports_count",
                 "delta_views_count", "delta_likes_count", "delta_comments_count", "delta_reports_count",
                 "created_at"}:
        return f"{base_alias}.{field}"

    raise ValueError(f"Unknown field: {field}")
