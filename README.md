# Compass
Simple, modular goal-setting and tracking

A guilt-free, low-friction daily logging system that emphasizes pattern recognition over performance pressure.

## Philosophy

- **Quick logging**: 15-30 seconds max
- **No guilt**: Partial completions are valid, streaks don't matter
- **Trend-focused**: Observe patterns, don't enforce goals
- **Modular**: Swap metrics in/out easily
- **Intelligent**: Local LLM provides insights without judgment

## Architecture

```
metrics_tracker/
├── app/
│   ├── __init__.py
│   ├── config.py              # Pydantic-based configuration
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── base.py            # MetricBase ABC and Pydantic models
│   │   ├── registry.py        # Metric discovery and management
│   │   └── implementations/   # Actual metric plugins
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py            # LLMInterface ABC
│   │   └── ollama.py          # Ollama implementation
│   ├── data/
│   │   └── database.py        # SQLite persistence
│   └── web/
│       ├── app.py             # Flask application 
│       ├── templates/         # HTML templates
│       └── static/            # CSS, JS
├── data/                      # SQLite database storage
├── config/                    # Configuration files
├── requirements.txt
└── README.md
```

## Core Contracts

### MetricBase
Every metric implements:
- `input_schema()` - Defines UI input type
- `validate(value)` - Validates user input
- `record(user_id, value)` - Stores entry
- `get_trends(user_id, days)` - Returns visualization data
- `get_aggregates(user_id, days)` - Returns summary stats
- `llm_prompt(user_id, context)` - Optional LLM integration

### LlmInterface
LLM providers implement:
- `generate_daily_summary()` - Morning insights
- `analyze_trend()` - Deep metric analysis
- `custom_prompt()` - Flexible Q&A
- `is_available()` - Health check

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python -m app.web.app
```

## Adding a New Metric

1. Create a new file in `app/metrics/implementations/`
2. Inherit from `MetricBase`
3. Implement all abstract methods
4. Register in the metric registry
5. Add to enabled metrics in config

Example:
```python
from app.metrics import MetricBase, MetricInputSchema

class MyMetric(MetricBase):
    @property
    def name(self) -> str:
        return "my_metric"
    
    # ... implement other methods
```
