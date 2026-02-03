"""Mood metric.

Track daily mood.
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

GREAT = "Great"
GOOD = "Good"
OKAY = "Okay"
POOR = "Poor"
BAD = "Bad"


class MoodMetric(MetricBase):
    """Track daily mood"""

    MOOD_OPTIONS = [GREAT, GOOD, OKAY, POOR, BAD]
    MOOD_VALUES = {GREAT: 5, GOOD: 4, OKAY: 3, POOR: 2, BAD: 1}

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
        return "mood"

    @property
    def display_name(self):
        return "Mood"

    @property
    def description(self):
        return "How would you describe your mood today?"

    def input_schema(self):
        return MetricInputSchema(
            input_type=InputType.SELECT,
            label="How would you describe your mood today?",
            required=False,
            options=self.MOOD_OPTIONS,
        )

    def validate(self, value: Any) -> bool:
        """Validate mood selection"""
        return value in self.MOOD_OPTIONS

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
        """Mood trend over time"""
        entries = self.entry_repo.get_for_user(
            user_id=user_id, metric_name=self.name, days=days
        )
        data_points = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "value": self.MOOD_VALUES.get(entry.value_text, 3),
                "date": entry.timestamp.strftime("%Y-%m-%d"),
                "label": entry.value_text,
            }
            for entry in reversed(entries)
        ]
        return MetricTrendData(
            metric_name=self.name,
            time_range_days=days,
            data_points=data_points,
            trend_type="categorical",
        )

    def get_aggregates(self, user_id, days):
        entries = self.entry_repo.get_for_user(
            user_id=user_id, metric_name=self.name, days=days
        )
        if not entries:
            return MetricAggregate(
                metric_name=self.name,
                time_range_days=days,
                summary="No mood data recorded.",
                stats={"count": 0},
            )
        mood_counts = {}
        for entry in entries:
            mood = entry.value_text
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        most_common = max(mood_counts.items(), key=lambda x: x[1])
        mood_values = [self.MOOD_VALUES.get(e.value_text, 3) for e in entries]
        avg_value = sum(mood_values) / len(mood_values)
        avg_mood = min(
            self.MOOD_OPTIONS, key=lambda m: abs(self.MOOD_VALUES[m] - avg_value)
        )
        summary = (
            f"Most common: {most_common[0]} ({most_common[1]}x) • Average: {avg_mood}"
        )
        return MetricAggregate(
            metric_name=self.name,
            time_range_days=days,
            summary=summary,
            stats={
                "count": len(entries),
                "most_common": most_common[0],
                "most_common_count": most_common[1],
                "average_mood": avg_mood,
                "distribution": mood_counts,
            },
        )
