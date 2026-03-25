# /src/utils/validation.py

import numpy as np
import pandas as pd
from typing import List, Tuple


def time_series_cv_by_date(
    df: pd.DataFrame,
    n_splits: int = 5,
    gap_days: int = 21,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate time-series cross-validation folds using calendar dates.
    

    Parameters
    ----------
    df : pd.DataFrame
        Input data with a 'date' column (datetime-like).
    n_splits : int, default=5
        Number of CV folds.
    gap_days : int, default=21
        Minimum calendar-day gap between train end and validation start.

    Returns
    -------
    folds : list of (train_idx, val_idx) tuples
        Each tuple contains:
        - train_idx: np.ndarray of integer indices for training set
        - val_idx: np.ndarray of integer indices for validation set

    Notes
    -----
    - Folds are created by splitting the date range into n_splits+1 segments
    - For each fold i:
        - Train: all data up to segment i
        - Validation: data in segment i+1, excluding the gap_days buffer
    - Rows within the gap window are excluded from validation
    """
    if "date" not in df.columns:
        raise ValueError("DataFrame must have a 'date' column")

    all_dates = np.sort(df["date"].unique())
    n_dates = len(all_dates)

    if n_splits < 2:
        raise ValueError("n_splits must be >= 2")
    if n_dates < n_splits + 1:
        raise ValueError(f"Not enough unique dates ({n_dates}) for {n_splits} splits")

    # Split date range into n_splits+1 segments
    segment_size = n_dates // (n_splits + 1)
    folds = []

    for i in range(n_splits):
        # Train: all data up to the end of segment i
        train_end_idx = (i + 1) * segment_size
        train_end_date = all_dates[train_end_idx - 1]

        # Validation: segment i+1, but excluding gap_days
        val_start_idx = train_end_idx
        val_end_idx = min((i + 2) * segment_size, n_dates)

        # Apply gap: validation starts gap_days after train_end_date
        val_start_date_adj = train_end_date + pd.Timedelta(days=gap_days)
        val_end_date = all_dates[val_end_idx - 1]

        # Get indices
        train_mask = df["date"] <= train_end_date
        val_mask = (df["date"] >= val_start_date_adj) & (df["date"] <= val_end_date)

        train_idx = np.where(train_mask)[0]
        val_idx = np.where(val_mask)[0]

        # Skip fold if validation set is empty after gap
        if len(val_idx) == 0:
            continue

        folds.append((train_idx, val_idx))

    return folds


def run_walkforward_cv_date_based(
    df: pd.DataFrame,
    feature_cols: List[str],
    label_col: str,
    model,
    n_splits: int = 5,
    gap_days: int = 21,
) -> pd.DataFrame:
    """
    Run walk-forward cross-validation with date-based gaps.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with features, label, and 'date' column.
    feature_cols : list of str
        Feature column names.
    label_col : str
        Binary label column name.
    model : sklearn-compatible estimator
        Model instance with fit() and predict_proba() methods.
        Will be cloned for each fold.
    n_splits : int, default=5
        Number of CV folds.
    gap_days : int, default=21
        Calendar-day gap between train and validation.

    Returns
    -------
    results : pd.DataFrame
        One row per fold with columns:
        - fold: fold number (0-indexed)
        - train_size: number of training samples
        - val_size: number of validation samples
        - train_pos_rate: positive label rate in training set
        - val_pos_rate: positive label rate in validation set
        - roc_auc: ROC AUC on validation set
        - avg_precision: Average Precision (PR-AUC) on validation set

    Notes
    -----
    - NaNs in features are filled with 0
    - Model is trained on each fold independently (no warm-start)
    - Returns empty DataFrame if no valid folds exist
    """
    from sklearn.metrics import roc_auc_score, average_precision_score
    from sklearn.base import clone

    folds = time_series_cv_by_date(df, n_splits=n_splits, gap_days=gap_days)

    if len(folds) == 0:
        print("Warning: No valid folds generated")
        return pd.DataFrame()

    results = []
    for fold_num, (train_idx, val_idx) in enumerate(folds):
        # Prepare data
        X_train = df.iloc[train_idx][feature_cols].fillna(0.0).values
        y_train = df.iloc[train_idx][label_col].astype(int).values

        X_val = df.iloc[val_idx][feature_cols].fillna(0.0).values
        y_val = df.iloc[val_idx][label_col].astype(int).values

        # Train model
        model_fold = clone(model)
        model_fold.fit(X_train, y_train)

        # Predict
        val_scores = model_fold.predict_proba(X_val)[:, 1]

        # Evaluate
        try:
            auc = roc_auc_score(y_val, val_scores)
            ap = average_precision_score(y_val, val_scores)
        except ValueError:
            # Handle edge case: only one class in y_val
            auc = np.nan
            ap = np.nan

        results.append(
            {
                "fold": fold_num,
                "train_size": len(train_idx),
                "val_size": len(val_idx),
                "train_pos_rate": y_train.mean(),
                "val_pos_rate": y_val.mean(),
                "roc_auc": auc,
                "avg_precision": ap,
            }
        )

    return pd.DataFrame(results)
