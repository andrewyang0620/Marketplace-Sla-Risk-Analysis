# /src/utils/eda.py
import pandas as pd
from config import SLA_THRESHOLDS


def quick_overview(df: pd.DataFrame, name: str) -> None:
    """Display quick overview statistics of a DataFrame.
    
    Prints shape, data types, and top 10 columns with highest missing value rates.
    
    Args:
        df: DataFrame to analyze.
        name: Display name for the DataFrame in output.
    """
    print(f"=== {name} ===")
    print(df.shape)
    print(df.dtypes)
    print(df.isna().mean().sort_values(ascending=False).head(10))
    print()


def time_coverage(table: pd.DataFrame, table_name: str, col_time: str) -> None:
    """Display time coverage statistics for a datetime column.
    
    Args:
        table: DataFrame containing the time column.
        table_name: Display name for the table in output.
        col_time: Name of the datetime column to analyze.
        
    Raises:
        KeyError: If col_time does not exist in the DataFrame.
    """
    if col_time not in table.columns:
        raise KeyError(f"Column '{col_time}' not found in {table_name} DataFrame")
        
    print(table_name)
    print(f"  Start: {table[col_time].min()}")
    print(f"  End:   {table[col_time].max()}")
    print(f"  Duration: {(table[col_time].max() - table[col_time].min()).days} days\n")


def show_delay_bucket(delay_series: pd.Series) -> None:
    """Show counts and rates of orders in each delay bucket defined by SLA_THRESHOLDS.
    
    Buckets are defined as:
    - Delay > extreme_threshold days
    - Delay (severe_threshold+1) to extreme_threshold days
    - Delay 1 to severe_threshold days
    - On-time or early delivery
    
    Args:
        delay_series: Series containing delay values in days.
    """
    s = delay_series.dropna()
    n = len(s)
    if n == 0:
        print("No valid delay data to summarize.")
        return

    any_delay = SLA_THRESHOLDS["any_delay"]
    severe_threshold = SLA_THRESHOLDS["severe_delay"]
    extreme_threshold = SLA_THRESHOLDS["extreme_delay"]

    extreme_delay = s > extreme_threshold
    severe_delay_window = (s > severe_threshold) & (s <= extreme_threshold)
    moderate_delay = (s > any_delay) & (s <= severe_threshold)
    on_time = s == 0
    early = s < 0

    def _show(name: str, mask: pd.Series) -> None:
        count = mask.sum()
        rate = count / n
        print(f"{name}: {count:,} ({rate:.2%})")

    _show(f"Delay >{extreme_threshold} days", extreme_delay)
    _show(f"Delay {severe_threshold+1}-{extreme_threshold} days", severe_delay_window)
    _show(f"Delay 1-{severe_threshold} days", moderate_delay)
    _show("On-time or early delivery", on_time | early)