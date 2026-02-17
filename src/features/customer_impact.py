# /src/features/customer_impact.py
import logging
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_order_customer_panel(
    orders_sellers: pd.DataFrame,
    order_reviews: pd.DataFrame,
    customers: pd.DataFrame,
    *,
    max_horizon_days: int = 30,  # repeat purchase time window
    low_rating_threshold: int = 3,  # review scores <= this are considered low ratings
    very_low_rating_threshold: int = 2,  # review scores <= this are considered very low ratings
) -> pd.DataFrame:
    """
    Build an order-level panel linking SLA metrics with customer experience outcomes.
    
    orders_sellers : pd.DataFrame
        Wide table at order + seller level that must contain at least:
          - order_id
          - customer_id
          - order_status
          - order_purchase_timestamp (datetime64[ns])
          - delay_days (numeric, can be negative for early deliveries)
          - is_sla_violation (bool or 0/1)
          - is_severe_violation (bool or 0/1)
    order_reviews : pd.DataFrame
        Order review table from Olist, expected to contain:
          - order_id
          - review_score (1-5)
          - review_creation_date (optional, for reference only)
    customers : pd.DataFrame
        Customer dimension table, expected to contain:
          - customer_id
        Additional attributes (e.g., city/state) will be preserved if present.
    max_horizon_days : int, optional
        Time window (in days) to define repeat purchase. Default is 30 days.
    low_rating_threshold : int, optional
        Threshold for low rating flag, inclusive. Default is 3 (<=3 is low).
    very_low_rating_threshold : int, optional
        Threshold for very low rating flag, inclusive. Default is 2 (<=2).

    Returns
    -------
    pd.DataFrame
        Order-level panel with the following additional columns:
          - review_score
          - review_creation_date (if available)
          - is_low_rating
          - is_very_low_rating
          - is_canceled
          - delay_bucket
          - next_order_time
          - days_to_next_order
          - repeat_within_horizon
        All original columns from `orders_sellers` and matching fields from
        `customers` are preserved.
    """
    
    df = orders_sellers.copy()
    
    # join with reviews
    rv = order_reviews.copy()
    # validate review has certain columns
    reviews_cols = [c for c in ["order_id", "review_score", "review_creation_date"] if c in rv.columns]
    if "order_id" not in reviews_cols or "review_score" not in reviews_cols:
        raise ValueError("order_reviews must contain at least 'order_id' and 'review_score'")
    
    # merge reviews into orders_sellers, keeping all orders
    df = df.merge(rv[reviews_cols], on="order_id", how="left")
    
    # rating flags
    df["is_low_rating"] = df["review_score"].le(low_rating_threshold)
    df["is_very_low_rating"] = df["review_score"].le(very_low_rating_threshold)
    
    # cancellation flag
    if "order_status" not in df.columns:
        raise ValueError("orders_sellers must contain 'order_status' column to determine cancellations")
    df["is_canceled"] = df["order_status"].eq("canceled")
    
    # delay buckets
    if "delay_days" not in df.columns:
        raise ValueError("orders_sellers must contain 'delay_days' column to create delay buckets")
    
    df["delay_bucket"] = pd.cut(
        df["delay_days"],
        bins=[-9999, 0, 2, 5, 9999],
        labels = ["on_time_or_early", "1-2_days_late", "3-5_days_late", "6+_days_late"],
        right=True,
        include_lowest=True
    )
    
    # join with customer dimensions
    if "customer_id" not in df.columns:
        raise ValueError("orders_sellers must contain 'customer_id' column to join with customers")
    cust_keep_cols = ["customer_id"]
    
    for col in ["customer_city", "customer_state"]:
        if col in customers.columns:
            cust_keep_cols.append(col)
    cust = customers[cust_keep_cols].drop_duplicates("customer_id")
    df = df.merge(cust, on="customer_id", how="left")
    
    # sort by customer and purchase timestamp to calculate repeat purchase metrics
    if not np.issubdtype(df["order_purchase_timestamp"].dtype, np.datetime64):
        raise ValueError("orders_sellers 'order_purchase_timestamp' must be datetime64[ns]")
    
    df = df.sort_values(["customer_id", "order_purchase_timestamp"])
    
    # next order per costumer
    df["next_order_time"] = df.groupby("customer_id")["order_purchase_timestamp"].shift(-1)
    df["days_to_next_order"] = (df["next_order_time"] - df["order_purchase_timestamp"]).dt.days
    
    # report purchase within horizon
    df["repeat_within_horizon"] = df["days_to_next_order"].between(0, max_horizon_days)
    
    return df