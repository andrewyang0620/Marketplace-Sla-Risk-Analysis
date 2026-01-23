# src/validation/data_quality.py
import pandas as pd
from config import DATA_QUALITY_THRESHOLDS

def validate_primary_keys(tables: dict) -> bool:
    """Validate primary keys for given tables.

    Args:
        tables (dict): Dictionary where keys are table names and values are tuples containing
                       the DataFrame and the primary key columns

    Returns:
        bool: True if all primary key validations pass, False otherwise.
    """
    all_ok = True
    for name, (df, key_cols) in tables.items():
        if isinstance(key_cols, str):
            key_cols = [key_cols]

        n_rows = len(df)
        n_keys = df[key_cols].drop_duplicates().shape[0]
        ok = (n_rows == n_keys)

        status = "PASSED" if ok else "FAILED"
        print(f"[PK {status}] {name}: {n_rows} rows, {n_keys} unique rows by {key_cols}")

        if not ok:
            all_ok = False

    print("\nOverall PK check:", "ALL PASSED" if all_ok else "SOME FAILED")
    return all_ok


def validate_foreign_keys(relations, min_match=1.0):
    """Validate foreign key relationships.

    Args:
        relations (list): List of tuples containing (name, child_df, child_col, parent_df, parent_col)
        min_match (float, optional): Minimum match rate to consider the validation passed. Defaults to 1.0.
    Returns:
        bool: True if all foreign key validations pass, False otherwise.
    """
    all_ok = True

    for name, child_df, child_col, parent_df, parent_col in relations:
        mask_not_null = child_df[child_col].notna()
        n_total = mask_not_null.sum()

        if n_total == 0:
            print(f"{name}: no non-null values in {child_col}")
            continue

        in_parent = child_df.loc[mask_not_null, child_col].isin(parent_df[parent_col])
        match_rate = in_parent.mean()

        ok = match_rate >= min_match
        status = "PASSED" if ok else "FAILED"
        print(
            f"[FK {status}]: "
            f"{match_rate:.4%} of non-null {child_col} values found in {parent_col} "
            f"({in_parent.sum()}/{n_total})"
        )

        if not ok:
            all_ok = False

    print("\nOverall FK check:", "ALL PASSED" if all_ok else "SOME FAILED")
    return all_ok


def validate_time_logic(table, time1, time2):
    """Validate logical order of two time columns in a table.

    Args:
        table (pd.DataFrame): DataFrame containing the time columns.
        time1 (str): Name of the first time column.
        time2 (str): Name of the second time column.

    Returns:
        bool: True if all records have time2 >= time1, False otherwise.
    """
    tlc = table[time2] < table[time1]
    m = tlc.mean()
    s = tlc.sum()
    if m == 0.0 and s == 0:
        return print(f"[PASSED]: All records have {time2} >= {time1}")
    else:
        return print(f"[FAILED]: {s} records have {time2} < {time1} {m:.4%} violation rate")
    
def compute_review_coverage(orders: pd.DataFrame, reviews: pd.DataFrame) -> float:
    """
    Compute the proportion of delivered orders that have valid customer reviews.
    Args:
        orders (pd.DataFrame): DataFrame containing order information.
        reviews (pd.DataFrame): DataFrame containing review information.
    Returns:
        float: Proportion of delivered orders with valid reviews.
    """
    delivered_orders = orders[orders["order_status"] == "delivered"].copy()
    n_delivered = delivered_orders["order_id"].nunique()

    valid_reviews = reviews[
        reviews["review_score"].between(1, 5) & reviews["review_score"].notna()
    ].copy()

    delivered_with_reviews = delivered_orders[["order_id"]].merge(
        valid_reviews[["order_id", "review_score"]],
        on="order_id",
        how="inner",
    )

    n_delivered_with_review = delivered_with_reviews["order_id"].nunique()

    if n_delivered == 0:
        return 0.0

    return n_delivered_with_review / n_delivered

def validate_review_coverage(orders: pd.DataFrame, reviews: pd.DataFrame, min_required: float | None = None) -> float:
    """
    Validate that the proportion of delivered orders with valid reviews meets the minimum required threshold.
    """
    if min_required is None:
        min_required = DATA_QUALITY_THRESHOLDS.get("min_review_coverage", 0.0)

    coverage = compute_review_coverage(orders, reviews)

    status = "PASSED" if coverage >= min_required else "FAILED"
    print(
        f"[REVIEW_COVERAGE {status}] "
        f"Delivered orders with valid review score: {coverage:.2%} "
        f"(min required: {min_required:.2%})"
    )

    return coverage

def validate_missing_sellers(orders_sellers: pd.DataFrame) -> None:
    """
    Validate and report the proportion of orders without assigned sellers.
    """
    missing = orders_sellers["seller_id"].isna()
    n_missing = missing.sum()
    rate_missing = missing.mean()

    print("\n=== Missing Seller Assignment Overview ===")
    print(
        f"Orders without seller assignment: "
        f"{n_missing:,} ({rate_missing:.4%})"
    )

    if n_missing > 0:
        print("\nMissing seller by order_status:")
        print(
            orders_sellers.loc[missing, "order_status"].value_counts()
        )

def validate_missing_by_column(df: pd.DataFrame, name: str = "df") -> None:
    """
    Print the proportion of missing values for each column in the DataFrame.
    """
    print(f"\n=== Missing values per column: {name} ===")
    for col in df.columns:
        missing_pct = df[col].isna().mean()
        print(f"  {col}: {missing_pct:.2%}")
