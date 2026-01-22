# /src/utils/eda.py
import pandas as pd

def quick_overview(df: pd.DataFrame, name: str) -> None:
    """Tool for quick overview of a dataframe"""
    print(f"=== {name} ===")
    print(df.shape)
    print(df.dtypes)
    print(df.isna().mean().sort_values(ascending=False).head(10))
    print()
    
def time_coverage(table, table_name, col_time):
    """Tool for checking time coverage of a time column in a table"""
    print(table_name)
    print(f"  Start: {table[col_time].min()}")
    print(f"  End:   {table[col_time].max()}")
    print(f"  Duration: {(table[col_time].max() - table[col_time].min()).days} days\n")
    
