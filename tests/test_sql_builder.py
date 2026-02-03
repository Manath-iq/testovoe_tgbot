from app.query_spec import QuerySpec
from app.sql_builder import build_sql


def test_count_videos_all():
    spec = QuerySpec(
        source="videos",
        aggregation="count",
        field=None,
        date_field=None,
        date_from=None,
        date_to=None,
        filters=[],
    )
    q = build_sql(spec)
    assert "count(*)" in q.sql
    assert "FROM videos v" in q.sql


def test_sum_delta_views_by_day():
    spec = QuerySpec(
        source="video_snapshots",
        aggregation="sum",
        field="delta_views_count",
        date_field="created_at",
        date_from="2025-11-28",
        date_to="2025-11-28",
        filters=[],
    )
    q = build_sql(spec)
    assert "sum(s.delta_views_count)" in q.sql
    assert "s.created_at >= $1" in q.sql
    assert "s.created_at < $2" in q.sql


def test_count_distinct_video_with_join():
    spec = QuerySpec(
        source="video_snapshots",
        aggregation="count_distinct",
        field="video_id",
        date_field="created_at",
        date_from="2025-11-27",
        date_to="2025-11-27",
        filters=[{"field": "creator_id", "op": "=", "value": "abc"}],
    )
    q = build_sql(spec)
    assert "JOIN videos v" in q.sql
    assert "v.creator_id = $3" in q.sql
