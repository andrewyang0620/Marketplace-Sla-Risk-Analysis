# /src/features/early_warning.py

from __future__ import annotations
from typing import Sequence, List
import numpy as np
import pandas as pd


def build_seller_daily_sla(
    orders_sellers: pd.DataFrame,
    delivered_only: bool = True,
) -> pd.DataFrame:
    """
    Build a daily seller-level SLA + GMV time series from the order-level table.

    This function:
      - (Optionally) filters to delivered orders.
      - Aggregates to (seller_id, date) level.
      - Computes daily counts:
          * delivered_orders
          * sla_violations
          * severe_violations
      - Computes daily GMV:
          * delivered_gmv
          * violation_gmv
          * severe_violation_gmv
      - Computes daily rates:
          * violation_rate, severe_violation_rate
          * violation_gmv_share, severe_violation_gmv_share
      - Adds lifetime cumulative metrics and seller tenure.

    Parameters
    ----------
    orders_sellers : pd.DataFrame
        Order-level table created in 00_data_validation and used in 01/02.
        Must contain at least:
          - seller_id
          - order_id
          - order_status
          - order_purchase_timestamp (datetime64[ns])
          - delay_days
          - is_sla_violation
          - is_severe_violation
          - order_gmv
    delivered_only : bool, default True
        If True, keep only rows where order_status == "delivered".
        For SLA reliability we typically focus on delivered orders.

    Returns
    -------
    pd.DataFrame
        Daily panel with one row per (seller_id, date) and columns:
          - seller_id
          - date
          - delivered_orders
          - sla_violations
          - severe_violations
          - avg_delay_days
          - delivered_gmv
          - violation_gmv
          - severe_violation_gmv
          - violation_rate
          - severe_violation_rate
          - violation_gmv_share
          - severe_violation_gmv_share
          - first_order_date
          - seller_tenure_days
          - cum_delivered_orders
          - cum_sla_violations
          - cum_severe_violations
          - cum_delivered_gmv
          - cum_violation_gmv
          - cum_severe_violation_gmv
          - lifetime_violation_rate
          - lifetime_severe_violation_rate
          - lifetime_violation_gmv_share
          - lifetime_severe_violation_gmv_share
    """
    df = orders_sellers.copy()

    required_cols = [
        "seller_id",
        "order_id",
        "order_status",
        "order_purchase_timestamp",
        "delay_days",
        "is_sla_violation",
        "is_severe_violation",
        "order_gmv",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"orders_sellers is missing required columns for early warning: {missing}"
        )

    if delivered_only:
        df = df[df["order_status"] == "delivered"].copy()

    if not np.issubdtype(df["order_purchase_timestamp"].dtype, np.datetime64):
        raise ValueError("order_purchase_timestamp must be datetime64[ns].")

    # Define event date as purchase date (consistent with 01/02 notebooks)
    df["date"] = df["order_purchase_timestamp"].dt.floor("D")

    # GMV-related columns: ensure no NaN to avoid weird sums
    df["order_gmv"] = df["order_gmv"].fillna(0.0)
    df["gmv_violation"] = np.where(df["is_sla_violation"] == 1, df["order_gmv"], 0.0)
    df["gmv_severe"] = np.where(df["is_severe_violation"] == 1, df["order_gmv"], 0.0)

    daily = (
        df.groupby(["seller_id", "date"])
        .agg(
            delivered_orders=("order_id", "nunique"),
            sla_violations=("is_sla_violation", "sum"),
            severe_violations=("is_severe_violation", "sum"),
            avg_delay_days=("delay_days", "mean"),
            delivered_gmv=("order_gmv", "sum"),
            violation_gmv=("gmv_violation", "sum"),
            severe_violation_gmv=("gmv_severe", "sum"),
        )
        .reset_index()
    )

    # Daily rates
    denom_orders = daily["delivered_orders"].replace({0: np.nan})
    denom_gmv = daily["delivered_gmv"].replace({0: np.nan})

    daily["violation_rate"] = daily["sla_violations"] / denom_orders
    daily["severe_violation_rate"] = daily["severe_violations"] / denom_orders
    daily["violation_gmv_share"] = daily["violation_gmv"] / denom_gmv
    daily["severe_violation_gmv_share"] = (
        daily["severe_violation_gmv"] / denom_gmv
    )

    # Sort and compute seller-level lifetime metrics
    daily = daily.sort_values(["seller_id", "date"])

    daily["first_order_date"] = daily.groupby("seller_id")["date"].transform("min")
    daily["seller_tenure_days"] = (
        daily["date"] - daily["first_order_date"]
    ).dt.days + 1

    daily["cum_delivered_orders"] = daily.groupby("seller_id")["delivered_orders"].cumsum()
    daily["cum_sla_violations"] = daily.groupby("seller_id")["sla_violations"].cumsum()
    daily["cum_severe_violations"] = daily.groupby("seller_id")["severe_violations"].cumsum()
    daily["cum_delivered_gmv"] = daily.groupby("seller_id")["delivered_gmv"].cumsum()
    daily["cum_violation_gmv"] = daily.groupby("seller_id")["violation_gmv"].cumsum()
    daily["cum_severe_violation_gmv"] = daily.groupby("seller_id")["severe_violation_gmv"].cumsum()

    denom_cum_orders = daily["cum_delivered_orders"].replace({0: np.nan})
    denom_cum_gmv = daily["cum_delivered_gmv"].replace({0: np.nan})

    daily["lifetime_violation_rate"] = (
        daily["cum_sla_violations"] / denom_cum_orders
    )
    daily["lifetime_severe_violation_rate"] = (
        daily["cum_severe_violations"] / denom_cum_orders
    )
    daily["lifetime_violation_gmv_share"] = (
        daily["cum_violation_gmv"] / denom_cum_gmv
    )
    daily["lifetime_severe_violation_gmv_share"] = (
        daily["cum_severe_violation_gmv"] / denom_cum_gmv
    )

    return daily


def build_rolling_seller_features(
    daily_df: pd.DataFrame,
    windows: Sequence[int] = (7, 14, 30),
    min_history_days: int = 7,
) -> pd.DataFrame:
    """
    Compute rolling-window features over daily SLA + GMV statistics.

    Windows are expressed in number of activity days per seller.

    Parameters
    ----------
    daily_df : pd.DataFrame
        Output of `build_seller_daily_sla`, must contain:
          - seller_id
          - date
          - delivered_orders
          - sla_violations
          - severe_violations
          - avg_delay_days
          - delivered_gmv
          - violation_gmv
          - severe_violation_gmv
          - seller_tenure_days
          - lifetime_violation_rate
          - lifetime_severe_violation_rate
          - lifetime_violation_gmv_share
          - lifetime_severe_violation_gmv_share
    windows : sequence of int, optional
        Rolling window sizes (in activity days) to compute features for.
        Typical choices: [7, 14, 30].
    min_history_days : int, optional
        Minimum seller tenure (in days since first order) required for a row to be kept in the resulting feature table.

    Returns
    -------
    pd.DataFrame
        Same rows as `daily_df` (after min_history_days filtering), with additional columns for each window size, for example for window=14:
          - delivered_14d
          - sla_violations_14d
          - severe_violations_14d
          - delivered_gmv_14d
          - violation_gmv_14d
          - severe_violation_gmv_14d
          - violation_rate_14d
          - severe_violation_rate_14d
          - violation_gmv_share_14d
          - severe_violation_gmv_share_14d
          - avg_delay_14d
    """
    df = daily_df.copy()
    df = df.sort_values(["seller_id", "date"])

    grp = df.groupby("seller_id", group_keys=False)

    for w in windows:
        roll = grp.rolling(window=w, min_periods=1)

        # Volume and counts
        df[f"delivered_{w}d"] = (
            roll["delivered_orders"].sum().reset_index(level=0, drop=True)
        )
        df[f"sla_violations_{w}d"] = (
            roll["sla_violations"].sum().reset_index(level=0, drop=True)
        )
        df[f"severe_violations_{w}d"] = (
            roll["severe_violations"].sum().reset_index(level=0, drop=True)
        )

        # GMV-side volumes
        df[f"delivered_gmv_{w}d"] = (
            roll["delivered_gmv"].sum().reset_index(level=0, drop=True)
        )
        df[f"violation_gmv_{w}d"] = (
            roll["violation_gmv"].sum().reset_index(level=0, drop=True)
        )
        df[f"severe_violation_gmv_{w}d"] = (
            roll["severe_violation_gmv"].sum().reset_index(level=0, drop=True)
        )

        # Rolling rates
        denom_orders = df[f"delivered_{w}d"].replace({0: np.nan})
        denom_gmv = df[f"delivered_gmv_{w}d"].replace({0: np.nan})

        df[f"violation_rate_{w}d"] = df[f"sla_violations_{w}d"] / denom_orders
        df[f"severe_violation_rate_{w}d"] = df[f"severe_violations_{w}d"] / denom_orders
        df[f"violation_gmv_share_{w}d"] = df[f"violation_gmv_{w}d"] / denom_gmv
        df[f"severe_violation_gmv_share_{w}d"] = (
            df[f"severe_violation_gmv_{w}d"] / denom_gmv
        )

        # Approximate rolling average delay
        df[f"avg_delay_{w}d"] = (
            roll["avg_delay_days"].mean().reset_index(level=0, drop=True)
        )

    # Drop rows with insufficient history if requested
    if "seller_tenure_days" in df.columns and min_history_days is not None:
        df = df[df["seller_tenure_days"] >= min_history_days].copy()

    return df