# /src/util/metrics.py
import pandas as pd
import numpy as np

def evaluate_topk_with_gmv(
    y_true: np.ndarray,
    scores: np.ndarray,
    future_gmv: np.ndarray,
    k_fracs: tuple = (0.01, 0.05, 0.10),
) -> pd.DataFrame:
    """
    Compute precision@K, event recall@K, GMV recall@K, and coverage for multiple K-fractions.

    Parameters
    ----------
    y_true : np.ndarray
        Binary ground-truth labels (0/1).
    scores : np.ndarray
        Predicted scores (higher = higher risk).
    future_gmv : np.ndarray
        Future severe-event GMV for each row (same shape as y_true).
        Typically `future_severe_gmv_{H}d`.
    k_fracs : tuple of float, optional
        Fractions of the population to flag (e.g. 0.01 = top 1%).

    Returns
    -------
    pd.DataFrame
        One row per K-fraction with columns:
          - k_frac
          - k
          - precision
          - event_recall
          - gmv_recall
          - coverage
    """
    y_true = np.asarray(y_true).astype(int)
    scores = np.asarray(scores)
    future_gmv = np.asarray(future_gmv).astype(float)

    n = len(y_true)
    order = np.argsort(-scores)  # descending by risk
    y_sorted = y_true[order]
    gmv_sorted = future_gmv[order]

    total_events = y_true.sum()
    total_gmv = future_gmv.sum()

    results = []
    for k_frac in k_fracs:
        k = max(1, int(n * k_frac))
        y_top = y_sorted[:k]
        gmv_top = gmv_sorted[:k]

        tp = y_top.sum()
        precision = tp / k
        event_recall = tp / total_events if total_events > 0 else np.nan

        gmv_captured = gmv_top.sum()
        gmv_recall = gmv_captured / total_gmv if total_gmv > 0 else np.nan

        coverage = k / n

        results.append(
            {
                "k_frac": k_frac,
                "k": k,
                "precision": precision,
                "event_recall": event_recall,
                "gmv_recall": gmv_recall,
                "coverage": coverage,
            }
        )

    return pd.DataFrame(results)