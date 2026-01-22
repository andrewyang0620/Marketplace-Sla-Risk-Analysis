# src/config.py
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_INTERIM = DATA_DIR / "interim"
DATA_PROCESSED = DATA_DIR / "processed"

# SLA Business Rules
SLA_THRESHOLDS = {
    'any_delay': 0,
    'severe_delay': 7,
    'extreme_delay': 30,
}

# Data validation thresholds
DATA_QUALITY_THRESHOLDS = {
    'min_delivery_rate': 0.95,
    'max_missing_seller': 0.01,
    'min_review_coverage': 0.90,
}
