"""Pydantic models for database entities"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.metrics.base import _InputType


class User(BaseModel):
    """User model"""

    id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes: bool = True


class UserMetricConfig(BaseModel):
    """Configuration for a user's metric"""

    id: Optional[int] = None
    user_id: int
    metric_name: str
    enabled: bool = True
    display_order: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes: bool = True


class MetricEntryDb(BaseModel):
    """Database representation of a metric entry.
    
    Note: This is different from MetricEntry in metrics.base,
    as this represents the database storage format.
    """
    id: Optional[int] = None
    user_id: int
    metric_name: str
    timestamp: datetime
    value_type: _InputType
    value_boolean: Optional[bool] = None
    value_integer: Optional[int] = None
    value_decimal: Optional[float] = None
    value_text: Optional[str] = None
    metadata: Optional[str] = None

    class Config:
        from_attributes: bool = True

    def get_value(self) -> Optional[object]:
        """Retrieve the value in its appropriate type based on value_type"""
        if self.value_type == _InputType.BOOLEAN:
            return self.value_boolean
        elif self.value_type == _InputType.INTEGER:
            return self.value_integer
        elif self.value_type == _InputType.DECIMAL:
            return self.value_decimal
        elif self.value_type == _InputType.TEXT:
            return self.value_text
        return None
