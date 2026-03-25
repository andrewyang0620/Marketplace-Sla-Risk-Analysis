# /src/features/sla_metrics.py
import pandas as pd
from config import SLA_THRESHOLDS

def calculate_delay_days(orders: pd.DataFrame) -> pd.DataFrame:
    """Calculate the delay in days between the actual delivery date and the estimated delivery date.

    Args:
        orders: DataFrame containing order information with 'order_delivered_customer_date' 
                and 'order_estimated_delivery_date' columns.

    Returns:
        Copy of the input DataFrame with an additional 'delay_days' column. 
        Values are pd.NA when either date is missing.
        
    Raises:
        KeyError: If required date columns are missing from the DataFrame.
    """
    required_cols = ["order_delivered_customer_date", "order_estimated_delivery_date"]
    for col in required_cols:
        if col not in orders.columns:
            raise KeyError(f"Column '{col}' not found in orders DataFrame")
    
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
    """Add boolean flags for SLA violations based on delay_days.
    
    Adds two columns:
    - is_sla_violation: True if delay_days > SLA_THRESHOLDS['any_delay'] (0 days)
    - is_severe_violation: True if delay_days > SLA_THRESHOLDS['severe_delay'] (7 days)
    
    Args:
        orders: DataFrame with 'order_delivered_customer_date' and 'delay_days' columns.
        
    Returns:
        Copy of input DataFrame with 'is_sla_violation' and 'is_severe_violation' columns added.
        
    Raises:
        KeyError: If 'delay_days' or 'order_delivered_customer_date' columns are missing.
    """
    required_cols = ["order_delivered_customer_date", "delay_days"]
    for col in required_cols:
        if col not in orders.columns:
            raise KeyError(f"Column '{col}' not found in orders DataFrame")
    
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
    """Categorize delay severity into predefined bins based on SLA_THRESHOLDS.
    
    Categories:
    - early: delay < 0
    - on_time: delay == 0
    - delay_1_7: 0 < delay <= severe_delay (7)
    - delay_8_30: severe_delay < delay <= extreme_delay (30)
    - delay_gt_30: delay > extreme_delay (30)
    
    Args:
        orders: DataFrame containing delay information.
        delay_col: Name of the column containing delay values. Defaults to 'delay_days'.
        out_col: Name for the output categorical column. Defaults to 'delay_severity'.
        
    Returns:
        Copy of input DataFrame with the categorical delay severity column added.
        
    Raises:
        KeyError: If delay_col does not exist in the DataFrame.
    """
    if delay_col not in orders.columns:
        raise KeyError(f"Column '{delay_col}' not found in orders DataFrame")
    
    df = orders.copy()
    s = df[delay_col]

    severe = SLA_THRESHOLDS["severe_delay"]      # 7
    extreme = SLA_THRESHOLDS["extreme_delay"]    # 30

    bins = [-float("inf"), -1, 0, severe, extreme, float("inf")]
    labels = ["early", "on_time", "delay_1_7", "delay_8_30", "delay_gt_30"]

    df[out_col] = pd.cut(s, bins=bins, labels=labels)

    return df

def get_sla_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """Generate a summary DataFrame with counts and rates of SLA violations.
    
    Args:
        orders: DataFrame containing order information with 'order_delivered_customer_date',
                'is_sla_violation', and 'is_severe_violation' columns.
                
    Returns:
        Summary DataFrame with columns ['Metric', 'Count', 'Rate (of delivered)'].
        Count values are formatted as comma-separated strings.
        Rate values are formatted as percentage strings.
        
    Raises:
        KeyError: If required columns are missing from the DataFrame.
    """
    required_cols = ["order_delivered_customer_date", "is_sla_violation", "is_severe_violation"]
    for col in required_cols:
        if col not in orders.columns:
            raise KeyError(f"Column '{col}' not found in orders DataFrame")
    
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
