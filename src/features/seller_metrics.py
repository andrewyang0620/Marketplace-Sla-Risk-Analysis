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

