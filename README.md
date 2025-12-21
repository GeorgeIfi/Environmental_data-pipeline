# UK Air Quality Data Pipeline

A data pipeline for processing UK air quality monitoring data using bronze/silver/gold architecture.

## Quick Start
```bash
pip install -r requirements.txt
python run_pipeline.py
```

## Structure
- `data/`: Raw, bronze, silver, gold data layers
- `src/`: Source code modules
- `sql/`: Data models and analytics queries
- `tests/`: Unit tests