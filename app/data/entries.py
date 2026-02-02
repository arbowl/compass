"""Data access layer for metric entries"""

from typing import Any, Optional
from datetime import datetime, timedelta
import json

from app.data.database import Database
from app.data.models import MetricEntryDb
from app.metrics.base import _InputType


class MetricEntryRepository:
    """Repository for metric entry operations"""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create(
        self,
        user_id: int,
        metric_name: str,
        value: Any,
        value_type: _InputType,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> MetricEntryDb:
        """Create a new metric entry"""
        if timestamp is None:
            timestamp = datetime.now()
        value_boolean = None
        value_integer = None
        value_decimal = None
        value_text = None
        if value_type == _InputType.BOOLEAN:
            value_boolean = bool(value)
        elif value_type == _InputType.INTEGER:
            value_integer = int(value)
        elif value_type == _InputType.DECIMAL:
            value_decimal = float(value)
        elif value_type == _InputType.TEXT:
            value_text = str(value)
        metadata_json = json.dumps(metadata) if metadata else None
        entry_id = self.db.execute_insert(
            """
            INSERT INTO metric_entries 
            (user_id, metric_name, timestamp, value_type, 
             value_boolean, value_integer, value_decimal, value_text, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, metric_name, timestamp, value_type,
             value_boolean, value_integer, value_decimal, value_text, metadata_json)
        )
        return self.get_by_id(entry_id)
    
    def get_by_id(self, entry_id: int) -> Optional[MetricEntryDb]:
        """Get a metric entry by ID."""
        row = self.db.execute_one(
            "SELECT * FROM metric_entries WHERE id = ?",
            (entry_id,)
        )
        return MetricEntryDb(**row) if row else None
    
    def get_for_user(
        self,
        user_id: int,
        metric_name: Optional[str] = None,
        days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[MetricEntryDb]:
        """Get metric entries for a user with optional filtering."""
        conditions = ["user_id = ?"]
        params = [user_id]
        if metric_name:
            conditions.append("metric_name = ?")
            params.append(metric_name)
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            conditions.append("timestamp >= ?")
            params.append(cutoff)
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        query = f"""
            SELECT * FROM metric_entries 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
        """
        rows = self.db.execute(query, tuple(params))
        return [MetricEntryDb(**row) for row in rows]
    
    def get_latest_for_metric(
        self,
        user_id: int,
        metric_name: str,
        limit: int = 1
    ) -> list[MetricEntryDb]:
        """Get the most recent entries for a specific metric."""
        rows = self.db.execute(
            """
            SELECT * FROM metric_entries
            WHERE user_id = ? AND metric_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, metric_name, limit)
        )
        return [MetricEntryDb(**row) for row in rows]
    
    def get_date_range_stats(
        self,
        user_id: int,
        metric_name: str,
        days: int
    ) -> dict:
        """Get basic statistics for a metric over a date range."""
        cutoff = datetime.now() - timedelta(days=days)
        row = self.db.execute_one(
            """
            SELECT 
                COUNT(*) as count,
                MIN(timestamp) as first_date,
                MAX(timestamp) as last_date
            FROM metric_entries
            WHERE user_id = ? AND metric_name = ? AND timestamp >= ?
            """,
            (user_id, metric_name, cutoff)
        )
        return row if row else {'count': 0, 'first_date': None, 'last_date': None}
    
    def delete(self, entry_id: int) -> bool:
        """Delete a metric entry."""
        self.db.execute(
            "DELETE FROM metric_entries WHERE id = ?",
            (entry_id,)
        )
        return True
    
    def delete_for_user(
        self, user_id: int, metric_name: Optional[str] = None
    ) -> int:
        """Delete all entries for a user, optionally filtered by metric."""
        if metric_name:
            query = "DELETE FROM metric_entries WHERE user_id = ? AND metric_name = ?"
            params = (user_id, metric_name)
        else:
            query = "DELETE FROM metric_entries WHERE user_id = ?"
            params = (user_id,)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            deleted = cursor.rowcount
            conn.commit()
        return deleted
