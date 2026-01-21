import pandas as pd


def quick_overview(df: pd.DataFrame, name: str) -> None:
    print(f"=== {name} ===")
    print(df.shape)
    print(df.dtypes)
    print(df.isna().mean().sort_values(ascending=False).head(10))
    print()


def show_delay_bucket():
    pass
