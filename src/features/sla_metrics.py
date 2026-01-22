# /src/features/sla_metrics.py
import pandas as pd
from src.config import SLA_THRESHOLDS

def calculate_delay_days(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()

    mask = df["order_delivered_customer_date"].notna() & df["order_estimated_delivery_date"].notna()

    df.loc[mask, "delay_days"] = (
        df.loc[mask, "order_delivered_customer_date"]- df.loc[mask, "order_estimated_delivery_date"]
    ).dt.days

    df.loc[~mask, "delay_days"] = pd.NA

    return df

def add_sla_violation_flags(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()

    delivered = df["order_delivered_customer_date"].notna()

    df["is_sla_violation"] = False
    df["is_severe_violation"] = False

    df.loc[delivered, "is_sla_violation"] = (
        df.loc[delivered, "delay_days"] > SLA_THRESHOLDS["any_delay"]
    )
    df.loc[delivered, "is_severe_violation"] = (
        df.loc[delivered, "delay_days"] > SLA_THRESHOLDS["severe_delay"]
    )

    return df

def classify_delay_severity():
    pass

def get_sla_summary():
    pass