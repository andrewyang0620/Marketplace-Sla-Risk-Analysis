import pandas as pd
from typing import List, Tuple, Dict


def validate_primary_keys(tables: dict) -> bool:
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
    tlc = table[time2] < table[time1]
    m = tlc.mean()
    s = tlc.sum()
    if m == 0.0 and s == 0:
        return print(f"[PASSED]: All records have {time2} >= {time1}")
    else:
        return print(f"[FAILED]: {s} records have {time2} < {time1} {m:.4%} violation rate")

def run_comprehensive_validation():
    pass