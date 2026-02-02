"""Daily notes metric.

Freeform text notes for seeding LLM prompts.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from app.metrics.base import (
    MetricBase,
    MetricInputSchema,
    MetricEntry,
    MetricTrendData,
    MetricAggregate,
    InputType,
)
from app.data import Database, MetricEntryRepository


class NotesMetric(MetricBase):
    """Track free-form daily notes"""

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
        return "notes"

    @property
    def display_name(self):
        return "Notes"

    @property
    def description(self):
        return "Any additional notes or observations?"

    def input_schema(self):
        return MetricInputSchema(
            input_type=InputType.TEXT,
            label="Any extra notes?",
            required=False,
            placeholder="How are you feeling? Any observations?"
        )

    def validate(self, value: Any) -> bool:
        """Notes are always valid (even empty strings)"""
        return True

    def record(self, user_id, value, timestamp = None):
        note_text = str(value) if value else ""
        if not note_text.strip():
            note_text = ""
        db_entry = self.entry_repo.create(
            user_id=user_id,
            metric_name=self.name,
            value=note_text,
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
        """Notes as a timeline"""
        entries = self.entry_repo.get_for_user(
            user_id=user_id,
            metric_name=self.name,
            days=days
        )
        entries_with_content = [
            e
            for e in entries
            if e.value_text and e.value_text.strip()
        ]
        data_points = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "value": entry.value_text,
                "date": entry.timestamp.strftime("%Y-%m-%d"),
                "preview": entry.value_text[:100]
                + "..." if len(entry.value_text) > 100 else entry.value_text
            }
            for entry in reversed(entries_with_content)
        ]
        return MetricTrendData(
            metric_name=self.name,
            time_range_days=days,
            data_points=data_points,
            trend_type="text",
        )

    def get_aggregates(self, user_id, days):
        entries = self.entry_repo.get_for_user(
            user_id=user_id,
            metric_name=self.name,
            days=days
        )
        entries_with_content = [
            e
            for e in entries
            if e.value_text and e.value_text.strip()
        ]
        if not entries_with_content:
            return MetricAggregate(
                metric_name=self.name,
                time_range_days=days,
                summary="No notes recorded.",
                stats={"count": 0, "total_words": 0}
            )
        total_words = sum(
            len(e.value_text.split()) for e in entries_with_content
        )
        avg_words = (
            total_words / len(entries_with_content)
            if entries_with_content
            else 0
        )
        recent_note = entries_with_content[0].value_text
        preview = (
            recent_note[:50] + "..."
            if len(recent_note) > 50
            else recent_note
        )
        summary = (
            f"{len(entries_with_content)} notes • ~{avg_words:.0f} "
            f"words/note • Latest: \"{preview}\""
        )
        return MetricAggregate(
            metric_name=self.name,
            time_range_days=days,
            summary=summary,
            stats={
                "count": len(entries_with_content),
                "total_words": total_words,
                "avg_words_per_note": round(avg_words, 1),
                "latest_preview": preview
            }
        )

    def llm_prompt(self, user_id, context = None) -> Optional[str]:
        """Generate LLM prompt for notes analysis."""
        entries = self.entry_repo.get_for_user(
            user_id=user_id,
            metric_name=self.name,
            days=7
        )
        entries_with_content = [
            e
            for e in entries
            if e.value_text and e.value_text.strip()
        ]
        if not entries_with_content:
            return None
        recent_notes = "\n".join([
            f"- {e.timestamp.strftime('%Y-%m-%d')}: {e.value_text}"
            for e in reversed(entries_with_content[-5:])
        ])
        prompt = f"""Based on recent daily notes:
{recent_notes}

Identify any patterns or themes in these notes (1-2 sentences)."""
        return prompt
