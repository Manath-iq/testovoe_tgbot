from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator

Source = Literal["videos", "video_snapshots"]
Aggregation = Literal["count", "count_distinct", "sum"]
MetricField = Literal[
    "id",
    "video_id",
    "creator_id",
    "video_created_at",
    "views_count",
    "likes_count",
    "comments_count",
    "reports_count",
    "delta_views_count",
    "delta_likes_count",
    "delta_comments_count",
    "delta_reports_count",
    "created_at",
]
DateField = Literal["video_created_at", "created_at"]
Op = Literal["=", ">", ">=", "<", "<="]


class Filter(BaseModel):
    field: MetricField
    op: Op
    value: str | int | float


class QuerySpec(BaseModel):
    source: Source
    aggregation: Aggregation
    field: MetricField | None = None
    date_field: DateField | None = None
    date_from: str | None = None
    date_to: str | None = None
    filters: list[Filter] = Field(default_factory=list)

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        # Expect YYYY-MM-DD
        if len(value) != 10:
            raise ValueError("Date must be YYYY-MM-DD")
        return value

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: MetricField | None, info):
        aggregation = info.data.get("aggregation")
        if aggregation == "sum" and value is None:
            raise ValueError("Field is required for sum")
        if aggregation == "count_distinct" and value is None:
            raise ValueError("Field is required for count_distinct")
        return value
