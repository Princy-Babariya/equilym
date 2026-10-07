"""Correlation Detection Module.

Calculates Pearson correlation matrices across numerical indicators and identifies
pairs exhibiting strong linear relationships above a configurable threshold.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from utils.constants import DEFAULT_CORRELATION_THRESHOLD
from analytics.preprocessing import get_numeric_columns


def compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute standard Pearson correlation matrix across numerical columns.

    Returns:
        Square symmetric pd.DataFrame of Pearson correlation coefficients.
    """
    if df.empty:
        return pd.DataFrame()

    if numeric_cols is None:
        numeric_cols = get_numeric_columns(df)

    valid_cols = [c for c in numeric_cols if c in df.columns]
    if len(valid_cols) < 2:
        return pd.DataFrame()

    numeric_df = df[valid_cols].apply(pd.to_numeric, errors="coerce")
    return numeric_df.corr(method="pearson").round(4)


def detect_significant_correlations(
    df: pd.DataFrame,
    threshold: float = DEFAULT_CORRELATION_THRESHOLD,
    numeric_cols: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Identify indicator pairs with |Pearson r| >= threshold.

    Returns:
        (significant_pairs_list, correlation_metadata)
    """
    if df.empty:
        return [], {"sample_size": 0, "warning": "Dataset is empty."}

    if numeric_cols is None:
        numeric_cols = get_numeric_columns(df)

    valid_cols = [c for c in numeric_cols if c in df.columns]
    if len(valid_cols) < 2:
        return [], {
            "sample_size": len(df),
            "warning": "Fewer than 2 numerical indicators available for correlation.",
        }

    numeric_df = df[valid_cols].apply(pd.to_numeric, errors="coerce").dropna()
    n_samples = len(numeric_df)

    warning_msg = None
    if n_samples < 20:
        warning_msg = (
            f"Correlation results may be unstable for small datasets (n = {n_samples}). "
            "Interpret with caution, as statistical significance requires larger samples."
        )

    corr_matrix = numeric_df.corr(method="pearson")
    pairs: List[Dict[str, Any]] = []

    # Iterate through upper triangle to avoid duplicates and self-correlation
    for i in range(len(valid_cols)):
        for j in range(i + 1, len(valid_cols)):
            col1 = valid_cols[i]
            col2 = valid_cols[j]
            r = corr_matrix.loc[col1, col2]

            if pd.isna(r):
                continue

            r_val = float(r)
            abs_r = abs(r_val)
            is_significant = abs_r >= threshold

            # Compute p-value using scipy if enough samples
            p_val = None
            if n_samples >= 3:
                try:
                    _, p = stats.pearsonr(numeric_df[col1], numeric_df[col2])
                    p_val = round(float(p), 4)
                except Exception:
                    p_val = None

            relationship = "positive" if r_val > 0 else "negative"

            pair_record = {
                "indicator_1": col1,
                "indicator_2": col2,
                "pair_label": f"{col1} vs {col2}",
                "correlation": round(r_val, 4),
                "absolute_correlation": round(abs_r, 4),
                "relationship": relationship,
                "is_significant": is_significant,
                "threshold_applied": threshold,
                "sample_size": n_samples,
                "p_value": p_val,
            }

            if is_significant:
                pairs.append(pair_record)

    # Sort descending by absolute correlation strength
    pairs.sort(key=lambda x: x["absolute_correlation"], reverse=True)

    metadata = {
        "sample_size": n_samples,
        "indicator_count": len(valid_cols),
        "threshold": threshold,
        "warning": warning_msg,
    }

    return pairs, metadata


def correlations_to_dataframe(pairs: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert correlation pair records to DataFrame."""
    if not pairs:
        return pd.DataFrame(
            columns=[
                "indicator_1",
                "indicator_2",
                "correlation",
                "absolute_correlation",
                "relationship",
                "p_value",
            ]
        )
    return pd.DataFrame(pairs)
