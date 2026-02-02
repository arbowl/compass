"""
Metrics module - defines the plugin system for tracking different data types.
"""

from app.metrics.base import (
    MetricBase,
    MetricInputSchema,
    MetricEntry,
    MetricTrendData,
    MetricAggregate
)
from app.metrics.registry import REGISTRY


__all__ = [
    "MetricBase",
    "MetricInputSchema", 
    "MetricEntry",
    "MetricTrendData",
    "MetricAggregate",
    "REGISTRY"
]
