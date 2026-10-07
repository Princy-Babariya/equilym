"""Trend Detection Module.

Calculates period-over-period percentage changes for each (district, indicator) pair.
Identifies significant trends based on a configurable threshold and returns structured records.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from utils.constants import DEFAULT_TREND_THRESHOLD
from analytics.preprocessing import get_numeric_columns


def detect_trends(
    df: pd.DataFrame,
    threshold_pct: float = DEFAULT_TREND_THRESHOLD,
    numeric_cols: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Detect significant trends across districts and indicators over consecutive time periods.

    Formula:
        pct_change = ((current_value - previous_value) / previous_value) * 100
        is_significant = abs(pct_change) >= threshold_pct

    Args:
        df: Preprocessed DataFrame sorted by district and month.
        threshold_pct: Significant change threshold in percent (e.g. 10.0 for 10%).
        numeric_cols: List of indicator columns to analyze.

    Returns:
        List of structured dictionaries representing detected period changes.
    """
    if df.empty or "district" not in df.columns or "month" not in df.columns:
        return []

    if numeric_cols is None:
        numeric_cols = get_numeric_columns(df)

    trend_records: List[Dict[str, Any]] = []

    # Group by district
    districts = df["district"].unique()

    for district in districts:
        district_df = df[df["district"] == district].sort_values("month")

        if len(district_df) < 2:
            continue

        for indicator in numeric_cols:
            if indicator not in district_df.columns:
                continue

            values = district_df[indicator].values
            months = district_df["month"].values

            for i in range(1, len(values)):
                prev_val = values[i - 1]
                curr_val = values[i]
                prev_month = months[i - 1]
                curr_month = months[i]

                # Skip if either is null/NaN
                if pd.isna(prev_val) or pd.isna(curr_val):
                    continue

                prev_val = float(prev_val)
                curr_val = float(curr_val)

                # Safe percentage change computation
                if prev_val == 0:
                    if curr_val == 0:
                        pct_change = 0.0
                    else:
                        pct_change = 100.0 if curr_val > 0 else -100.0
                else:
                    pct_change = ((curr_val - prev_val) / abs(prev_val)) * 100.0

                pct_change_rounded = round(pct_change, 2)
                abs_change = round(curr_val - prev_val, 2)
                is_significant = abs(pct_change_rounded) >= threshold_pct

                if pct_change_rounded > 0:
                    direction = "increased"
                elif pct_change_rounded < 0:
                    direction = "decreased"
                else:
                    direction = "unchanged"

                record = {
                    "district": str(district),
                    "indicator": str(indicator),
                    "previous_period": str(prev_month),
                    "current_period": str(curr_month),
                    "previous_value": prev_val,
                    "current_value": curr_val,
                    "absolute_change": abs_change,
                    "change_pct": pct_change_rounded,
                    "direction": direction,
                    "threshold_applied": threshold_pct,
                    "is_significant": is_significant,
                }
                trend_records.append(record)

    return trend_records


def filter_significant_trends(trend_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only trends flagged as significant."""
    return [r for r in trend_records if r.get("is_significant", False)]


def trends_to_dataframe(trend_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert trend record dicts into a structured DataFrame."""
    if not trend_records:
        return pd.DataFrame(
            columns=[
                "district",
                "indicator",
                "previous_period",
                "current_period",
                "previous_value",
                "current_value",
                "change_pct",
                "direction",
                "is_significant",
            ]
        )
    return pd.DataFrame(trend_records)
