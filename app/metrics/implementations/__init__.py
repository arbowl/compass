"""Metric implementations.

This module imports all metric implementations and registers them
with the global registry.
"""

from app.data import Database
from app.metrics.registry import REGISTRY
from app.metrics.implementations.notes import NotesMetric


def register_all_metrics(db: Database) -> None:
    """Register all available metric implementations."""
    metrics = [
        NotesMetric(db)
    ]
    for metric in metrics:
        REGISTRY._instances[metric.name] = metric
        REGISTRY._metrics[metric.name] = metric.__class__


__all__ = [
    "NotesMetric",
    "register_all_metrics"
]
