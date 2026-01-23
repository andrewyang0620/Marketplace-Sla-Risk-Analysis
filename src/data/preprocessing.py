# src/data/preprocessing.py
import pandas as pd

def sellect_primary_seller(items: pd.DataFrame, primary_item_id: int = 1) -> pd.DataFrame:
    """
    Select the primary seller for each order based on the order_item_id.
    """
    items_main = items.loc[
        items["order_item_id"] == primary_item_id,["order_id", "seller_id"],
    ].copy()
    
    return items_main

def build_orders_sellers(orders: pd.DataFrame, items: pd.DataFrame, primary_item_id: int = 1, cols_keep: list[str] | None = None) -> pd.DataFrame:
    """
    Build a DataFrame that links orders with their primary sellers.
    """
    items_main = sellect_primary_seller(items, primary_item_id=primary_item_id)

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