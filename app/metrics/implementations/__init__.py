"""Metric implementations.

This module imports all metric implementations and registers them
with the global registry.
"""

from typing import TYPE_CHECKING

from app.data import Database
from app.metrics.implementations.alone import AloneTimeMetric
from app.metrics.implementations.exercise import ExerciseMetric
from app.metrics.implementations.groceries import GroceriesMetric
from app.metrics.implementations.mood import MoodMetric
from app.metrics.implementations.notes import NotesMetric
from app.metrics.implementations.scale import ScaleMetric
from app.metrics.registry import REGISTRY
if TYPE_CHECKING:
    from app.metrics.base import MetricBase


def register_all_metrics(db: Database) -> None:
    """Register all available metric implementations."""
    metrics: list[MetricBase] = [
        NotesMetric(db),
        GroceriesMetric(db),
        ScaleMetric(db),
        ExerciseMetric(db),
        AloneTimeMetric(db),
        MoodMetric(db),
    ]
    for metric in metrics:
        REGISTRY._instances[metric.name] = metric
        REGISTRY._metrics[metric.name] = metric.__class__


__all__ = [
    "NotesMetric",
    "GroceriesMetric",
    "ScaleMetric",
    "ExerciseMetric",
    "AloneTimeMetric",
    "MoodMetric",
    "register_all_metrics",
]
