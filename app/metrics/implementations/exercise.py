"""Exercise metric.

Track daily exercise completion.
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


class ExerciseMetric(MetricBase):
    """Track daily exercise"""

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
        return "exercise"

    @property
    def display_name(self):
        return "Exercise"

    @property
    def description(self):
        return "Did you exercise today?"

    def input_schema(self):
        return MetricInputSchema(
            input_type=InputType.SELECT,
            label="Did you exercise today?",
            required=False,
            options=["Yes", "No"],
        )

    def validate(self, value: Any) -> bool:
        """Validate yes/no input"""
        return value in ["Yes", "No"]

    def record(self, user_id, value, timestamp=None):
        db_entry = self.entry_repo.create_or_update(
            user_id=user_id,
            metric_name=self.name,
            value=value,
            value_type=InputType.TEXT,
            timestamp=timestamp,
        )
        return MetricEntry(
            user_id=db_entry.user_id,
            metric_name=db_entry.metric_name,
            timestamp=db_entry.timestamp,
            value=db_entry.value_text,
        )

    def get_trends(self, user_id, days):
        """Boolean trend over time"""
        entries = self.entry_repo.get_for_user(
            user_id=user_id,
            metric_name=self.name,
            days=days
        )
        data_points = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "value": 1 if entry.value_text == "Yes" else 0,
                "date": entry.timestamp.strftime("%Y-%m-%d"),
                "label": entry.value_text
            }
            for entry in reversed(entries)
        ]
        return MetricTrendData(
            metric_name=self.name,
            time_range_days=days,
            data_points=data_points,
            trend_type="boolean",
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
                summary="No exercise data recorded.",
                stats={"count": 0, "yes_count": 0, "percentage": 0}
            )
        yes_count = sum(1 for e in entries if e.value_text == "Yes")
        total_count = len(entries)
        percentage = (yes_count / total_count * 100) if total_count > 0 else 0
        summary = (
            f"{yes_count}/{total_count} days exercised "
            f"({percentage:.0f}%)"
        )
        return MetricAggregate(
            metric_name=self.name,
            time_range_days=days,
            summary=summary,
            stats={
                "count": total_count,
                "yes_count": yes_count,
                "no_count": total_count - yes_count,
                "percentage": round(percentage, 1)
            }
        )
