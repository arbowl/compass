"""Pydantic models for all data structures"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel


class InputType(StrEnum):
    """Types of inputs for UI fields"""

    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    INTEGER = "integer"
    TEXT = "text"
    SELECT = "select"


class MetricInputSchema(BaseModel):
    """Defines the input schema for a metric and tells the UI how to render
    the input field.
    """

    input_type: InputType
    label: str
    required: bool = False
    options: Optional[list[str]] = None  # For SELECT type
    placeholder: Optional[str] = None
    min_value: Optional[float] = None  # For DECIMAL and INTEGER types
    max_value: Optional[float] = None  # For DECIMAL and INTEGER types

    class Config:
        frozen: bool = True


class MetricEntry(BaseModel):
    """Represents a single metric entry/log"""

    user_id: int
    metric_name: str
    timestamp: datetime
    value: Any
    metadata: Optional[dict[str, Any]] = None


class MetricTrendData(BaseModel):
    """Trend data returned by a metric for visualization"""

    metric_name: str
    time_range_days: int
    data_points: list[dict[str, Any]]
    trend_type: str


class MetricAggregate(BaseModel):
    """Aggregate statistics for a metric over a time period"""

    metric_name: str
    time_range_days: int
    summary: str
    stats: dict[str, Any]


class MetricBase(ABC):
    """Abstract base class for all metrics.

    Each metric defines:
    - What input it accepts (via input_schema)
    - How to validate that input
    - How to store entries
    - How to compute trends
    - How to generate aggregates
    - Optionally, custom LLM prompts
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this metric"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for this metric"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this metric tracks"""
        pass

    @abstractmethod
    def input_schema(self) -> MetricInputSchema:
        """Returns the input schema for this metric"""
        pass

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validates user input before storage.
        Returns True if valid, False otherwise.
        """
        pass

    @abstractmethod
    def record(
        self,
        user_id: int,
        value: Any,
        timestamp: Optional[datetime] = None,
    ) -> MetricEntry:
        """Records a new metric entry/log"""
        pass

    @abstractmethod
    def get_trends(
        self,
        user_id: int,
        days: int,
    ) -> MetricTrendData:
        """Computes trend data for visualization over the given time range"""
        pass

    @abstractmethod
    def get_aggregates(
        self,
        user_id: int,
        days: int,
    ) -> MetricAggregate:
        """Generates aggregate statistics over the given time range"""
        pass

    def llm_prompt(
        self,
        user_id: int,
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Optional LLM prompt customization for this metric"""
        return None
