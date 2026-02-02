"""Alone time metric.

Track hours of alone time per day.
"""

from typing import Any, Optional

from app.data import Database, MetricEntryRepository
from app.metrics.base import (
    InputType,
    MetricAggregate,
    MetricBase,
    MetricEntry,
    MetricInputSchema,
    MetricTrendData,
)


class AloneTimeMetric(MetricBase):
    """Track hours of alone time"""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db
        self._entry_repo = None

    @property
    def entry_repo(self) -> MetricEntryRepository:
        """Lazy load the entry repository"""
        if self._entry_repo is None and self.db is not None:
            self._entry_repo = MetricEntryRepository(self.db)
        return self._entry_repo

    @property
    def name(self):
        return "alone_time"

    @property
    def display_name(self):
        return "Alone Time"

    @property
    def description(self):
        return "How many hours of alone time did you have today?"

    def input_schema(self):
        return MetricInputSchema(
            input_type=InputType.DECIMAL,
            label="How many hours of alone time did you have today?",
            required=False,
            min_value=0.0,
            max_value=24.0,
        )

    def validate(self, value: Any) -> bool:
        """Validate numeric input"""
        try:
            float_value = float(value)
            return 0.0 <= float_value <= 24.0
        except (ValueError, TypeError):
            return False

    def record(self, user_id, value, timestamp=None):
        decimal_value = round(float(value), 1)
        db_entry = self.entry_repo.create(
            user_id=user_id,
            metric_name=self.name,
            value=decimal_value,
            value_type=InputType.DECIMAL,
            timestamp=timestamp,
        )
        return MetricEntry(
            user_id=db_entry.user_id,
            metric_name=db_entry.metric_name,
            timestamp=db_entry.timestamp,
            value=db_entry.value_decimal,
        )

    def get_trends(self, user_id, days):
        """Hours trend over time"""
        entries = self.entry_repo.get_for_user(
            user_id=user_id,
            metric_name=self.name,
            days=days
        )
        data_points = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "value": round(entry.value_decimal, 1),
                "date": entry.timestamp.strftime("%Y-%m-%d"),
            }
            for entry in reversed(entries)
        ]
        return MetricTrendData(
            metric_name=self.name,
            time_range_days=days,
            data_points=data_points,
            trend_type="line",
        )

    def get_aggregates(self, user_id, days):
        entries = self.entry_repo.get_for_user(
            user_id=user_id,
            metric_name=self.name,
            days=days
        )
        if not entries:
            return MetricAggregate(
                metric_name=self.name,
                time_range_days=days,
                summary="No alone time data recorded.",
                stats={"count": 0}
            )
        values = [e.value_decimal for e in entries]
        total = sum(values)
        avg = total / len(values)
        min_val = min(values)
        max_val = max(values)
        summary = (
            f"Avg: {avg:.1f} hrs/day • "
            f"Total: {total:.1f} hrs • "
            f"Range: {min_val:.1f}-{max_val:.1f}"
        )
        return MetricAggregate(
            metric_name=self.name,
            time_range_days=days,
            summary=summary,
            stats={
                "count": len(entries),
                "total": round(total, 1),
                "average": round(avg, 1),
                "min": round(min_val, 1),
                "max": round(max_val, 1)
            }
        )
