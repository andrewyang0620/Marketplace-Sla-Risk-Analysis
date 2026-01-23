# src/data/preprocessing.py
import pandas as pd

def select_primary_seller(items: pd.DataFrame, primary_item_id: int = 1) -> pd.DataFrame:
    """Select the primary seller for each order based on the order_item_id.
    
    Args:
        items: DataFrame containing order items with 'order_item_id', 'order_id', and 'seller_id' columns.
        primary_item_id: The order_item_id value to consider as primary. Defaults to 1.
        
    Returns:
        DataFrame with columns ['order_id', 'seller_id'] for orders matching the primary_item_id.
        
    Raises:
        KeyError: If required columns are missing from the items DataFrame.
    """
    required_cols = ["order_item_id", "order_id", "seller_id"]
    for col in required_cols:
        if col not in items.columns:
            raise KeyError(f"Column '{col}' not found in items DataFrame")
    
    items_main = items.loc[
        items["order_item_id"] == primary_item_id,["order_id", "seller_id"],
    ].copy()
    
    return items_main

def build_orders_sellers(orders: pd.DataFrame, items: pd.DataFrame, primary_item_id: int = 1, cols_keep: list[str] | None = None) -> pd.DataFrame:
    """Build a DataFrame that links orders with their primary sellers.
    
    Args:
        orders: DataFrame containing order information with 'order_id' column.
        items: DataFrame containing order item information.
        primary_item_id: The order_item_id to consider as primary. Defaults to 1.
        cols_keep: List of columns to keep in the final DataFrame. If None, keep all columns. Defaults to None.
        
    Returns:
        DataFrame linking orders with their primary sellers. Includes 'has_time_anomaly' column (defaulting to False).
        
    Raises:
        KeyError: If 'order_id' is missing from orders, or if cols_keep specifies missing columns.
    """
    if "order_id" not in orders.columns:
        raise KeyError("Column 'order_id' not found in orders DataFrame")
    
    items_main = select_primary_seller(items, primary_item_id=primary_item_id)

    df = orders.merge(
        items_main,
        on="order_id",
        how="left",
    )
    
    if "has_time_anomaly" not in df.columns:
        df["has_time_anomaly"] = False
        
    if cols_keep is not None:
        missing_cols = [c for c in cols_keep if c not in df.columns]
        if missing_cols:
            raise KeyError(f"Columns not found in orders_sellers: {missing_cols}")
        df = df[cols_keep]

    return df