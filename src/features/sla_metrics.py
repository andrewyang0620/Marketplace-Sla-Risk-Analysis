# /src/features/sla_metrics.py
import pandas as pd
from config import SLA_THRESHOLDS

def calculate_delay_days(orders: pd.DataFrame) -> pd.DataFrame:
    """Calculate the delay in days between the actual delivery date and the estimated delivery date.

    Args:
        orders (pd.DataFrame): DataFrame containing order information with delivery dates.

    Returns:
        pd.DataFrame: DataFrame with an additional column "delay_days" representing the delay in days.
    """
    df = orders.copy()

    mask = df["order_delivered_customer_date"].notna() & df["order_estimated_delivery_date"].notna()

    # delay calculation
    df.loc[mask, "delay_days"] = (
        df.loc[mask, "order_delivered_customer_date"]- df.loc[mask, "order_estimated_delivery_date"]
    ).dt.days
    
    df.loc[~mask, "delay_days"] = pd.NA
    # return updated dataframe with delay_days column
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

def classify_delay_severity(orders: pd.DataFrame, delay_col: str = "delay_days", out_col: str = "delay_severity") -> pd.DataFrame:
    """
    Use SLA_THRESHOLDS to categorize delay severity into bins:

      early        : delay < 0
      on_time      : delay == 0
      delay_1_7    : 1 <= delay <= severe_delay
      delay_8_30   : severe_delay+1 <= delay <= extreme_delay
      delay_gt_30  : delay > extreme_delay
    """
    df = orders.copy()
    s = df[delay_col]

    severe = SLA_THRESHOLDS["severe_delay"]      # 7
    extreme = SLA_THRESHOLDS["extreme_delay"]    # 30

    bins = [-float("inf"), -1, 0, severe, extreme, float("inf")]
    labels = ["early", "on_time", "delay_1_7", "delay_8_30", "delay_gt_30"]

    df[out_col] = pd.cut(s, bins=bins, labels=labels)

    return df

def get_sla_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a summary DataFrame with counts and rates of SLA violations.
    Args:
        orders (pd.DataFrame): DataFrame containing order information with SLA violation flags.
    Returns:
        pd.DataFrame: Summary DataFrame with counts and rates of SLA violations.
    """
    delivered = orders["order_delivered_customer_date"].notna()

    sla_violations = orders.loc[delivered, "is_sla_violation"]
    severe_violations = orders.loc[delivered, "is_severe_violation"]

    summary = pd.DataFrame({
        "Metric": [
            "Orders with any delay (SLA violation)",
            f"Orders with severe delay (>{SLA_THRESHOLDS['severe_delay']} days)",
        ],
        "Count": [
            sla_violations.sum(),
            severe_violations.sum(),
        ],
        "Rate (of delivered)": [
            sla_violations.mean(),
            severe_violations.mean(),
        ],
    })
    summary["Count"] = summary["Count"].map(lambda x: f"{x:,}")
    summary["Rate (of delivered)"] = summary["Rate (of delivered)"].map(
        lambda x: f"{x:.2%}"
    )

    return summary
