"""Data access layer for daily summary cache."""

from datetime import date, datetime
from typing import Optional

from app.data.database import Database
from app.data.models import DailySummaryCache


class SummaryCacheRepository:
    """Repository for daily summary cache operations."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_for_user_date(
        self, user_id: int, cache_date: date
    ) -> Optional[DailySummaryCache]:
        """Get cached summary for a user on a specific date."""
        row = self.db.execute_one(
            """
            SELECT * FROM daily_summary_cache
            WHERE user_id = ? AND cache_date = ?
            """,
            (user_id, cache_date.isoformat()),
        )
        return DailySummaryCache(**row) if row else None

    def create(self, user_id: int, cache_date: date, summary_content: str) -> int:
        """Store a new cached summary. Returns the inserted ID."""
        return self.db.execute_insert(
            """
            INSERT INTO daily_summary_cache (user_id, cache_date, summary_content, generated_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, cache_date.isoformat(), summary_content, datetime.now()),
        )
