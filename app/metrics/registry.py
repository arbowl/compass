"""Metric registry for managing available metrics.

This module handles loading, registering, and dynamic access.
"""

from app.metrics.base import MetricBase


class MetricRegistry:
    """Central registry for all available metrics.

    Metrics register themselves here, and the orchestration layer
    queries this registry to determine which metrics are available.
    """

    def __init__(self) -> None:
        self._metrics: dict[str, MetricBase] = {}
        self._instances: dict[str, MetricBase] = {}

    def register(self, metric_class: type[MetricBase]) -> None:
        """Register a new metric class."""
        instance = metric_class()
        name = instance.name
        self._metrics[name] = metric_class
        self._instances[name] = instance

    def get(self, name: str) -> MetricBase:
        """Get a metric instance by name."""
        if name not in self._instances:
            raise KeyError(f"Metric '{name}' not found in registry.")
        return self._instances[name]

    def get_all(self) -> list[MetricBase]:
        """Get all registered metric instances."""
        return list(self._instances.values())

    def get_enabled(self, enabled_names: list[str]) -> list[MetricBase]:
        """Get all enabled metric instances."""
        return [
            self._instances[name]
            for name in enabled_names
            if name in self._instances
        ]

    def is_registered(self, name: str) -> bool:
        """Check if a metric is registered."""
        return name in self._instances


REGISTRY = MetricRegistry()
