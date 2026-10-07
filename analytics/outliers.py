"""Outlier Detection Module.

Implements Interquartile Range (IQR) and standard deviation Z-score statistical
outlier detection across numerical indicators.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from utils.constants import DEFAULT_OUTLIER_METHOD, DEFAULT_ZSCORE_THRESHOLD
from analytics.preprocessing import get_numeric_columns


def detect_outliers_iqr(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    iqr_multiplier: float = 1.5,
) -> List[Dict[str, Any]]:
    """Detect outliers using the Interquartile Range (Tukey's Fences) method.

    Formula:
        Q1 = 25th percentile
        Q3 = 75th percentile
        IQR = Q3 - Q1
        Lower Bound = Q1 - 1.5 * IQR
        Upper Bound = Q3 + 1.5 * IQR
        Outlier condition: value < Lower Bound OR value > Upper Bound
    """
    if df.empty:
        return []

    if numeric_cols is None:
        numeric_cols = get_numeric_columns(df)

    outliers: List[Dict[str, Any]] = []

    for indicator in numeric_cols:
        if indicator not in df.columns:
            continue

        series = df[indicator].dropna()
        if len(series) < 4:
            # Need minimum data points for meaningful quartiles
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - (iqr_multiplier * iqr)
        upper_bound = q3 + (iqr_multiplier * iqr)
        median = float(series.median())
        mean = float(series.mean())

        for idx, row in df.iterrows():
            val = row.get(indicator)
            if pd.isna(val):
                continue
            val = float(val)

            is_lower = val < lower_bound
            is_upper = val > upper_bound

            if is_lower or is_upper:
                distance = (lower_bound - val) if is_lower else (val - upper_bound)
                bound_breached = "below_lower" if is_lower else "above_upper"
                outliers.append({
                    "district": str(row.get("district", "Unknown")),
                    "indicator": str(indicator),
                    "month": str(row.get("month", "Unknown")),
                    "value": val,
                    "method": "IQR",
                    "q1": round(q1, 2),
                    "q3": round(q3, 2),
                    "iqr": round(iqr, 2),
                    "lower_bound": round(lower_bound, 2),
                    "upper_bound": round(upper_bound, 2),
                    "mean": round(mean, 2),
                    "median": round(median, 2),
                    "distance_from_bound": round(distance, 2),
                    "bound_breached": bound_breached,
                    "score": round(distance / (iqr if iqr > 0 else 1.0), 2),
                })

    return outliers


def detect_outliers_zscore(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    threshold: float = DEFAULT_ZSCORE_THRESHOLD,
) -> List[Dict[str, Any]]:
    """Detect outliers using standard deviation Z-score.

    Formula:
        z = (value - mean) / std
        Outlier condition: abs(z) >= threshold
    """
    if df.empty:
        return []

    if numeric_cols is None:
        numeric_cols = get_numeric_columns(df)

    outliers: List[Dict[str, Any]] = []

    for indicator in numeric_cols:
        if indicator not in df.columns:
            continue

        series = df[indicator].dropna()
        if len(series) < 3:
            continue

        mean = float(series.mean())
        std = float(series.std(ddof=1))

        if std == 0 or np.isnan(std):
            continue

        lower_bound = mean - (threshold * std)
        upper_bound = mean + (threshold * std)
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1

        for idx, row in df.iterrows():
            val = row.get(indicator)
            if pd.isna(val):
                continue
            val = float(val)

            z = (val - mean) / std

            if abs(z) >= threshold:
                distance = abs(val - mean) - (threshold * std)
                bound_breached = "below_lower" if z < 0 else "above_upper"
                outliers.append({
                    "district": str(row.get("district", "Unknown")),
                    "indicator": str(indicator),
                    "month": str(row.get("month", "Unknown")),
                    "value": val,
                    "method": "Z-Score",
                    "z_score": round(z, 2),
                    "threshold": threshold,
                    "mean": round(mean, 2),
                    "std": round(std, 2),
                    "lower_bound": round(lower_bound, 2),
                    "upper_bound": round(upper_bound, 2),
                    "q1": round(q1, 2),
                    "q3": round(q3, 2),
                    "iqr": round(iqr, 2),
                    "distance_from_bound": round(distance, 2),
                    "bound_breached": bound_breached,
                    "score": round(abs(z), 2),
                })

    return outliers


def detect_outliers(
    df: pd.DataFrame,
    method: str = DEFAULT_OUTLIER_METHOD,
    z_threshold: float = DEFAULT_ZSCORE_THRESHOLD,
    numeric_cols: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Unified outlier detection dispatcher based on selected method ('IQR' or 'Z-Score')."""
    if method.upper() == "Z-SCORE":
        return detect_outliers_zscore(df, numeric_cols=numeric_cols, threshold=z_threshold)
    return detect_outliers_iqr(df, numeric_cols=numeric_cols)


def outliers_to_dataframe(outlier_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert outlier records to a formatted DataFrame."""
    if not outlier_records:
        return pd.DataFrame(
            columns=[
                "district",
                "indicator",
                "month",
                "value",
                "method",
                "lower_bound",
                "upper_bound",
            ]
        )
    return pd.DataFrame(outlier_records)
