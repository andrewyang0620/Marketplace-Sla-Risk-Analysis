# /src/features/seller_metrics.py
import logging
from typing import Dict, Optional, Sequence, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# some required columns for seller metrics calculation
REQUIRED_COLS = {
    "order_id",
    "seller_id",
    "order_status",
    "order_purchase_timestamp",
    "is_sla_violation",
    "is_severe_violation",
    "delay_days",
}

# allowed order status
ALLOWED_STATUSES = {
    "delivered",
    "canceled",
    "shipped",
    "invoiced",
    "processing",
    "created",
    "unavailable",
}


def validate_orders_sellers(
    df: pd.DataFrame,
    gmv_col: Optional[str] = None,
) -> None:
    """Validate the orders_sellers DataFrame for required columns, data types, and consistency.

    Args:
        df (pd.DataFrame): DataFrame containing orders and sellers data.
        gmv_col (Optional[str], optional): Column name for Gross Merchandise Value. Defaults to None.
    """
    
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"orders_sellers missing required columns: {missing}")

    # check order_purchase_timestamp dtype
    if not np.issubdtype(df["order_purchase_timestamp"].dtype, np.datetime64):
        raise ValueError(
            "order_purchase_timestamp must be datetime64[ns]. "
            "Please convert before calling seller metrics."
        )

    # check order_status values
    unique_status = set(df["order_status"].dropna().unique())
    unknown_status = unique_status - ALLOWED_STATUSES
    if unknown_status:
        logger.warning(
            "orders_sellers contains unexpected order_status values: %s",
            unknown_status,
        )

    # check for duplicate key pairs
    dup_mask = df.duplicated(subset=["order_id", "seller_id"])
    dup_cnt = dup_mask.sum()
    if dup_cnt > 0:
        raise ValueError(
            f"Duplicate (order_id, seller_id) pairs detected: {dup_cnt}. "
            "This may indicate data join issues."
        )

    # report missing rates (log only, no error)
    na_rates = df[list(REQUIRED_COLS)].isna().mean()
    logger.info("NA rates in orders_sellers (required columns):\n%s", na_rates)

    # check GMV column if specified
    if gmv_col is not None:
        if gmv_col not in df.columns:
            raise ValueError(f"gmv_col '{gmv_col}' not found in dataframe.")
        if not np.issubdtype(df[gmv_col].dtype, np.number):
            raise ValueError(f"gmv_col '{gmv_col}' must be numeric.")

def _apply_time_window(
    df: pd.DataFrame,
    as_of: Optional[pd.Timestamp] = None,
    lookback_days: Optional[int] = None,
) -> Tuple[pd.DataFrame, Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Apply a time window filter to the orders_sellers DataFrame based on as_of date and lookback_days.
    Args:
        df: DataFrame containing orders_sellers data with 'order_purchase_timestamp' column.
        as_of: The end date of the time window. If None, use the max timestamp in the data.
        lookback_days: Number of days to look back from as_of. If None, use the full range.
    Returns:
        Filtered DataFrame and the (start, end) timestamps of the applied window.
    """
    ts = df["order_purchase_timestamp"]

    if as_of is None:
        as_of = ts.max()

    if lookback_days is not None:
        start = as_of - pd.Timedelta(days=lookback_days)
        mask = (ts >= start) & (ts <= as_of)
        df_win = df.loc[mask].copy()
        return df_win, (start, as_of)
    else:
        return df.copy(), (ts.min(), ts.max())
    

def compute_seller_sla_metrics(
    orders_sellers: pd.DataFrame,
    *,
    gmv_col: Optional[str] = None,
    severe_weight: float = 2.0,
    as_of: Optional[pd.Timestamp] = None,
    lookback_days: Optional[int] = None,
) -> pd.DataFrame:
    """
    Use orders_sellers DataFrame to compute seller-level SLA metrics over a specified time window.

    gmv_col: keep for future use (not used currently)

    Output fields (core):
      - seller_id
      - period_start, period_end      : Time window boundaries (for record and audit)
      - total_orders_all_status       : Total order count across all statuses (deduplicated)
      - delivered_orders              : Count of delivered orders
      - canceled_orders               : Count of canceled orders
      - pending_orders                : Count of other status orders (non-delivered / non-canceled)

      - sla_violations                : Count of delivered orders with is_sla_violation=True
      - severe_violations             : Count of delivered orders with is_severe_violation=True
      - violation_rate                : sla_violations / delivered_orders
      - severe_violation_rate         : severe_violations / delivered_orders
      - avg_delay_days                : Average delay_days for delivered orders

      - severity_weighted_violations  : sla_violations + severe_weight * severe_violations
    """
    df = orders_sellers.copy()
    validate_orders_sellers(df, gmv_col=gmv_col)

    # time window filtering
    df_win, (start, end) = _apply_time_window(df, as_of=as_of, lookback_days=lookback_days)

    # num of orders by seller
    grp_all = df_win.groupby("seller_id", as_index=True)
    total_orders_all_status = grp_all["order_id"].nunique()

    # split by status
    delivered_mask = df_win["order_status"] == "delivered"
    canceled_mask = df_win["order_status"] == "canceled"

    df_delivered = df_win[delivered_mask].copy()
    df_canceled = df_win[canceled_mask].copy()
    df_pending = df_win[~(delivered_mask | canceled_mask)].copy()

    delivered_orders = df_delivered.groupby("seller_id")["order_id"].nunique()
    canceled_orders = df_canceled.groupby("seller_id")["order_id"].nunique()
    pending_orders = df_pending.groupby("seller_id")["order_id"].nunique()

    # align indices
    # new DataFrame to hold metrics
    metrics = pd.DataFrame(index=total_orders_all_status.index)
    metrics["total_orders_all_status"] = total_orders_all_status
    metrics["delivered_orders"] = delivered_orders.reindex(metrics.index, fill_value=0)
    metrics["canceled_orders"] = canceled_orders.reindex(metrics.index, fill_value=0)
    metrics["pending_orders"] = pending_orders.reindex(metrics.index, fill_value=0)

    # ===== SLA related =====
    if len(df_delivered) > 0:
        grp_deliv = df_delivered.groupby("seller_id", as_index=True)

        sla_violations = grp_deliv["is_sla_violation"].sum(min_count=1)
        severe_violations = grp_deliv["is_severe_violation"].sum(min_count=1)
        avg_delay_days = grp_deliv["delay_days"].mean()

        metrics["sla_violations"] = sla_violations.reindex(metrics.index, fill_value=0)
        metrics["severe_violations"] = severe_violations.reindex(metrics.index, fill_value=0)
        metrics["avg_delay_days"] = avg_delay_days.reindex(metrics.index)
    else:
        metrics["sla_violations"] = 0
        metrics["severe_violations"] = 0
        metrics["avg_delay_days"] = np.nan

    # violation rates
    with np.errstate(divide="ignore", invalid="ignore"):
        metrics["violation_rate"] = np.where(
            metrics["delivered_orders"] > 0,
            metrics["sla_violations"] / metrics["delivered_orders"],
            np.nan,
        )
        metrics["severe_violation_rate"] = np.where(
            metrics["delivered_orders"] > 0,
            metrics["severe_violations"] / metrics["delivered_orders"],
            np.nan,
        )

    metrics["severity_weighted_violations"] = (
        metrics["sla_violations"] + severe_weight * metrics["severe_violations"]
    )

    # time window info
    metrics["period_start"] = start
    metrics["period_end"] = end

    metrics = metrics.reset_index().rename(columns={"index": "seller_id"})
    return metrics
