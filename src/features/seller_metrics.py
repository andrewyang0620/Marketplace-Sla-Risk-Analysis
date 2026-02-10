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

def rank_sellers_by_sla_risk(
    seller_metrics: pd.DataFrame,
    *,
    min_delivered_orders: int = 10,
    risk_weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """Rank sellers by SLA risk and calculate risk_score based on SLA metrics.

    Current version uses only SLA dimensions:
      - violation_rate
      - severity_weighted_violations

    Steps:
      1. Filter out sellers with delivered_orders < min_delivered_orders (small sample noise).
      2. Calculate quantile rank (0~1) for each feature, treating missing values as 0.
      3. Compute risk_score as weighted sum based on risk_weights.
      4. Sort by risk_score in descending order.
      5. Calculate:
         - cum_violation_share
         - cum_severity_share
         - seller_rank, seller_rank_share
    """
    df = seller_metrics.copy()

    df = df[df["delivered_orders"] >= min_delivered_orders].copy()
    if df.empty:
        logger.warning("No sellers left after applying min_delivered_orders filter.")
        df["risk_score"] = []
        return df

    # Default weights - pure SLA perspective
    if risk_weights is None:
        risk_weights = {
            "violation_rate": 0.5,
            "severity_weighted_violations": 0.5,
        }

    def pct_rank(series: pd.Series) -> pd.Series:
        """Percentile rank, returns 0 if all values are missing."""
        if series.notna().sum() == 0:
            return pd.Series(0.0, index=series.index)
        return series.rank(pct=True)

    # Build rank features
    rank_features = {}
    for feature in risk_weights.keys():
        if feature not in df.columns:
            raise ValueError(f"Feature '{feature}' not found in seller_metrics.")
        rank_features[feature] = pct_rank(df[feature].fillna(0.0))

    # Combine risk_score
    risk_score = np.zeros(len(df), dtype=float)
    for feature, weight in risk_weights.items():
        risk_score += weight * rank_features[feature].to_numpy()
    df["risk_score"] = risk_score

    # Sort by risk from high to low
    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)

    # Cumulative share (violations and severity)
    total_viol = df["sla_violations"].sum()
    total_severity = df["severity_weighted_violations"].sum()

    if total_viol > 0:
        df["cum_violation_share"] = df["sla_violations"].cumsum() / total_viol
    else:
        df["cum_violation_share"] = 0.0

    if total_severity > 0:
        df["cum_severity_share"] = (
            df["severity_weighted_violations"].cumsum() / total_severity
        )
    else:
        df["cum_severity_share"] = 0.0

    # For Lorenz / Pareto curve
    n_sellers = len(df)
    df["seller_rank"] = np.arange(1, n_sellers + 1)
    df["seller_rank_share"] = df["seller_rank"] / n_sellers

    return df


def assign_risk_tier_by_quantile(
    ranked: pd.DataFrame,
    *,
    high_q: float = 0.9,
    medium_q: float = 0.6,
    min_orders_high: int = 50,
    min_orders_medium: int = 20,
    col: str = "risk_score",
) -> pd.DataFrame:
    """Assign risk tier based on quantiles of the specified column (default: risk_score).

    Sellers with very few delivered orders may be assigned to lower tiers even if their risk_score is high, due to higher uncertainty.

    Args:
        ranked: DataFrame output from rank_sellers_by_sla_risk, must contain 'delivered_orders' and the specified col.
        high_q: Quantile threshold for High Risk tier.
        medium_q: Quantile threshold for Medium Risk tier.
        min_orders_high: Minimum delivered orders to be considered for High Risk tier.
        min_orders_medium: Minimum delivered orders to be considered for Medium Risk tier.
        col: Column name to use for quantile calculation (default: 'risk_score').

    Returns:
        DataFrame with an additional 'risk_tier' column indicating 'High', 'Medium', or 'Low' risk.
    """
    df = ranked.copy()
    if df.empty:
        df["risk_tier"] = []
        return df
    
    high_thr = df[col].quantile(high_q)  # 90th percentile as threshold for High Risk
    med_thr = df[col].quantile(medium_q)  # 60th percentile as threshold for Medium Risk
    
    conditions = [
        (df[col] >= high_thr) & (df["delivered_orders"] >= min_orders_high),
        (df[col] >= med_thr) & (df[col] < high_thr) & (df["delivered_orders"] >= min_orders_medium),
    ]
    choices = ["high", "medium"]
    
    df["risk_tier"] = np.select(conditions, choices, default="low")
    return df


def compute_seller_metrics_by_period(
    orders_sellers: pd.DataFrame,
    *,
    gmv_col: Optional[str] = None,
    severe_weight: float = 2.0,
    freq: str = "M",
) -> pd.DataFrame:
    """Compute seller metrics by period for trend analysis.
    This function groups the orders_sellers data by the specified time frequency (e.g., monthly) and computes seller SLA metrics for each period. The output DataFrame contains seller-level metrics for each time period, allowing for trend analysis and monitoring of SLA performance over time.
    Args:
    orders_sellers: DataFrame containing orders and sellers data with required columns.
    gmv_col: Optional column name for Gross Merchandise Value, currently not used in calculations but validated for future use.
    severe_weight: Weight factor for severe violations when calculating severity_weighted_violations.
    freq: Time frequency for grouping periods (e.g., 'D' for daily, 'W' for weekly, 'M' for monthly).
    """
    df = orders_sellers.copy()
    validate_orders_sellers(df, gmv_col=gmv_col)
    
    df["period"] = df["order_purchase_timestamp"].dt.to_period(freq)
    results = []
    
    for period, sub in df.groupby("period"):
        metrics = compute_seller_sla_metrics(
            sub,
            gmv_col=gmv_col,
            severe_weight=severe_weight,
            as_of = sub["order_purchase_timestamp"].max(),  # end of the period
            lookback_days=None,  # use all data up to the end of the period
        )
        metrics["period"] = period
        results.append(metrics)
        
    if not results:
        return pd.DataFrame()
    
    return pd.concat(results, ignore_index=True)
