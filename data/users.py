"""Data accesss layer for user-related operations."""

from typing import Optional
from datetime import datetime

from app.data.database import Database
from app.data.models import User, UserMetricConfig


class UserRepository:
    """Repository for CRUD operations."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, name: str) -> User:
        """Create a new user."""
        user_id = self.db.execute_insert(
            "INSERT INTO users (name, created_at, updated_at) VALUES (?, ?, ?)",
            (name, datetime.now(), datetime.now())
        )
        return self.get_by_id(user_id)

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        row = self.db.execute_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        return User(**row) if row else None

    def get_by_name(self, name: str) -> Optional[User]:
        """Retrieve a user by name."""
        row = self.db.execute_one(
            "SELECT * FROM users WHERE name = ?",
            (name,)
        )
        return User(**row) if row else None

    def get_all(self) -> list[User]:
        """Retrieve all users."""
        rows = self.db.execute(
            "SELECT * FROM users ORDER BY name"
        )
        return [User(**row) for row in rows]

    def update(self, user_id: int, name: str) -> Optional[User]:
        """Update a user's name"""
        self.db.execute(
            "UPDATE users SET name = ?, updated_at = ? WHERE id = ?",
            (name, datetime.now(), user_id)
        )
        return self.get_by_id(user_id)

    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        self.db.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        return True

    def get_enabled_metrics(self, user_id: int) -> list[UserMetricConfig]:
        """Get all enabled metrics for a user."""
        rows = self.db.execute(
            """
            SELECT metric_name 
            FROM user_metrics 
            WHERE user_id = ? AND enabled = 1
            ORDER BY display_order, metric_name
            """,
            (user_id,)
        )
        return [row["metric_name"] for row in rows]

    def set_metric_enabled(
        self,
        user_id: int,
        metric_name: str,
        enabled: bool,
    ) -> None:
        """Enable or disable a metric for a user."""
        existing = self.db.execute_one(
            "SELECT id FROM user_metrics WHERE user_id = ? AND metric_name = ?",
            (user_id, metric_name)
        )
        if existing:
            self.db.execute(
                "UPDATE user_metrics SET enabled = ? WHERE user_id = ? AND metric_name = ?",
                (enabled, user_id, metric_name)
            )
        else:
            self.db.execute_insert(
                "INSERT INTO user_metrics (user_id, metric_name, enabled) VALUES (?, ?, ?)",
                (user_id, metric_name, enabled)
            )

    def initialize_user_metrics(
        self, user_id: int, metric_names: list[str]
    ) -> None:
        """Initialize default metrics for a new user."""
        for i, metric_name in enumerate(metric_names):
            existing = self.db.execute_one(
                "SELECT id FROM user_metrics WHERE user_id = ? AND metric_name = ?",
                (user_id, metric_name)
            )
            if not existing:
                self.db.execute_insert(
                    """
                    INSERT INTO user_metrics (user_id, metric_name, enabled, display_order) 
                    VALUES (?, ?, 1, ?)
                    """,
                    (user_id, metric_name, i)
                )
