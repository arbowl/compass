"""Ollama LLM implementation"""

from typing import Any, Optional

import requests
from requests.exceptions import RequestException, Timeout

from app.llm.base import (
    LlmInterface,
    LlmMessage,
    LlmResponse,
    DailySummaryRequest,
    TrendAnalysisRequest,
    Role,
)


class OllamaLlm(LlmInterface):
    """Ollama LLM provider implementation"""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen3:4b",
        timeout: int = 30,
    ) -> None:
        """Initialize the Ollama LLM provider"""
        self.host: str = host
        self.model: str = model
        self.timeout: int = timeout
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if the Ollama server is reachable"""
        if self._available is not None:
            return self._available
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            self._available = response.status_code == 200
        except RequestException:
            self._available = False
        return self._available

    def _generate(
        self,
        messages: list[LlmMessage],
        max_tokens: int = 500,
    ) -> str:
        """Generate a response from the Ollama model"""
        if not self.is_available():
            return LlmResponse(
                content="LLM service is not available",
                metadata={"error": "service_unavailable"},
            )
        prompt_parts = []
        for msg in messages:
            if msg.role == Role.SYSTEM:
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == Role.USER:
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == Role.ASSISTANT:
                prompt_parts.append(f"Assistant: {msg.content}")
        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                    },
                },
                timeout=self.timeout,
            )
            if response.status_code != 200:
                return LlmResponse(
                    content=f"Ollama API error: {response.status_code}",
                    metadata={
                        "error": "api_error",
                        "status_code": response.status_code,
                    },
                )
            result: dict[str, str] = response.json()
            content = result.get("response", "").strip()
            return LlmResponse(
                content=content,
                metadata={
                    "model": self.model,
                    "done": result.get("done", False),
                },
            )
        except Timeout:
            return LlmResponse(
                content="LLM request timed out",
                metadata={"error": "timeout"},
            )
        except RequestException as e:
            return LlmResponse(
                content=f"Error communicating with LLM: {str(e)}",
                metadata={"error": "communication_error"},
            )
        except Exception as e:
            return LlmResponse(
                content=f"Unexpected error: {str(e)}",
                metadata={"error": "unexpected_error"},
            )

    def generate_daily_summary(self, request: DailySummaryRequest) -> LlmResponse:
        """Generate a daily summary based on metrics data"""
        metrics_summary = self._format_metrics_data(request.metrics_data)
        messages = [
            LlmMessage(
                role=Role.SYSTEM,
                content=(
                    "You're a supportive health tracking assistant. "
                    "Provide brief, encouraging insights based on user data. "
                    "Keep responses to 1-2 friendly sentences. No lectures, "
                    "just positive observations."
                ),
            ),
            LlmMessage(
                role=Role.USER,
                content=(
                    f"Based on my recent tracking data:\n{metrics_summary}\n"
                    "\nGive me a brief, encouraging message for today "
                    "(1-2 sentences)."
                ),
            ),
        ]
        return self._generate(messages, max_tokens=150)

    def analyze_trend(self, request: TrendAnalysisRequest) -> LlmResponse:
        """Analyze a trend based on metric data"""
        trend_summary = self._format_trend_data(request.trend_data, indent=2)
        messages = [
            LlmMessage(
                role=Role.SYSTEM,
                content=(
                    "You are a data analysis assistant focused on health "
                    "metrics. Provide objective, actionable insights without "
                    "being preachy. Focus on patterns and observations."
                ),
            ),
            LlmMessage(
                role=Role.USER,
                content=(
                    f"Analyze this {request.time_range_days}-day trend for "
                    f"{request.metric_name}:\n{trend_summary}\n\n"
                    "What patterns do you notice? Keep it brief "
                    "(1-3 sentences)."
                ),
            ),
        ]
        return self._generate(messages, max_tokens=300)

    def custom_prompt(self, messages: list[LlmMessage]) -> LlmResponse:
        """Generate a response to a custom prompt"""
        return self._generate(messages, max_tokens=500)

    def _format_metrics_data(self, metrics_data: dict[str, Any]) -> str:
        """Format metrics data for the LLM"""
        if not metrics_data:
            return "No recent data available."
        parts = []
        for metric_name, data in metrics_data.items():
            if isinstance(data, dict):
                summary = data.get("summary", "No summary available.")
                parts.append(f"- {metric_name}:\n  {summary}")
            else:
                parts.append(f"- {metric_name}: {data}")
        return "\n".join(parts) if parts else "No recent data available."
