"""Severity Classification Module.

Derives objective Low / Medium / High severity rankings mathematically
from statistical thresholds rather than arbitrary magic numbers.
"""

from typing import Union
from utils.constants import (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    DEFAULT_TREND_THRESHOLD,
    DEFAULT_ZSCORE_THRESHOLD,
)


def calculate_trend_severity(
    change_pct: float,
    threshold_pct: float = DEFAULT_TREND_THRESHOLD,
) -> str:
    """Classify trend severity based on the relative ratio to the significant threshold.

    Formula:
        relative_ratio = abs(change_pct) / threshold_pct

    Classification Rules:
        - Low:    relative_ratio < 1.5   (change is between 1.0x and 1.5x threshold)
        - Medium: 1.5 <= relative_ratio < 2.5 (change is between 1.5x and 2.5x threshold)
        - High:   relative_ratio >= 2.5  (change is >= 2.5x threshold)
    """
    if threshold_pct <= 0:
        threshold_pct = 1.0

    ratio = abs(change_pct) / threshold_pct

    if ratio < 1.5:
        return SEVERITY_LOW
    elif ratio < 2.5:
        return SEVERITY_MEDIUM
    else:
        return SEVERITY_HIGH


def calculate_iqr_outlier_severity(
    distance_from_bound: float,
    iqr: float,
) -> str:
    """Classify IQR outlier severity based on relative excess beyond the boundary.

    Formula:
        excess_ratio = distance_from_bound / IQR (or 1.0 if IQR is 0)

    Classification Rules:
        - Low:    excess_ratio < 0.5 (just outside Tukey fences)
        - Medium: 0.5 <= excess_ratio < 1.0 (moderately beyond fences)
        - High:   excess_ratio >= 1.0 (extreme outlier, >= 1 full IQR beyond boundary)
    """
    effective_scale = iqr if iqr > 0 else 1.0
    ratio = abs(distance_from_bound) / effective_scale

    if ratio < 0.5:
        return SEVERITY_LOW
    elif ratio < 1.0:
        return SEVERITY_MEDIUM
    else:
        return SEVERITY_HIGH


def calculate_zscore_outlier_severity(
    z_score: float,
    threshold: float = DEFAULT_ZSCORE_THRESHOLD,
) -> str:
    """Classify Z-score outlier severity based on how far z exceeds the threshold.

    Formula:
        z_ratio = abs(z_score) / threshold

    Classification Rules:
        - Low:    z_ratio < 1.25 (e.g., 3.0 <= |z| < 3.75 for threshold=3)
        - Medium: 1.25 <= z_ratio < 1.67 (e.g., 3.75 <= |z| < 5.0)
        - High:   z_ratio >= 1.67 (e.g., |z| >= 5.0)
    """
    if threshold <= 0:
        threshold = 3.0

    ratio = abs(z_score) / threshold

    if ratio < 1.25:
        return SEVERITY_LOW
    elif ratio < 1.67:
        return SEVERITY_MEDIUM
    else:
        return SEVERITY_HIGH


def calculate_correlation_severity(abs_r: float) -> str:
    """Classify correlation strength severity based on absolute Pearson r.

    Classification Rules:
        - Low:    |r| < 0.80  (strong association above threshold)
        - Medium: 0.80 <= |r| < 0.90 (very strong linear association)
        - High:   |r| >= 0.90 (near-deterministic collinearity or critical anomaly correlation)
    """
    val = abs(abs_r)
    if val < 0.80:
        return SEVERITY_LOW
    elif val < 0.90:
        return SEVERITY_MEDIUM
    else:
        return SEVERITY_HIGH
