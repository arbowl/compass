"""Base models for the LLM layer"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Optional


from pydantic import BaseModel


class _Role(Enum):
    """LLM role"""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()


class LlmMessage(BaseModel):
    """A single message in an LLM conversation"""

    role: _Role
    content: str


class LlmResponse(BaseModel):
    """Response from an LLM query"""

    content: str
    metadata: Optional[dict[str, Any]] = None


class DailySummaryRequest(BaseModel):
    """Request model for generating daily summaries"""

    user_id: int
    metrics_data: dict[str, Any]


class TrendAnalysisRequest(BaseModel):
    """Request model for generating trend analysis"""

    user_id: int
    metric_name: str
    time_range_days: int
    trend_data: dict[str, Any]


class LlmInterface(ABC):
    """Abstract base class for LLM providers.
    
    This allows swapping out Ollama for OpenAI, Anthropic, or any other
    LLM provider without changing the rest of the application.
    """

    @abstractmethod
    def generate_daily_summary(
        self, request: DailySummaryRequest
    ) -> LlmResponse:
        """Generate a daily summary based on metrics data"""
        pass

    @abstractmethod
    def analyze_trend(
        self, request: TrendAnalysisRequest
    ) -> LlmResponse:
        """Analyze a trend based on metric data"""
        pass

    @abstractmethod
    def custom_prompt(
        self, messages: list[LlmMessage]
    ) -> LlmResponse:
        """Generate a response to a custom prompt"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass
