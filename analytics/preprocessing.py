"""Data Preprocessing Module for Healthcare Performance CSV.

Cleans input DataFrames, standardizes date formats, coerces numeric fields,
sorts chronologically by district and month, and prepares tidy tabular representations.
"""

from typing import List, Tuple
import pandas as pd
from utils.constants import DEFAULT_NUMERIC_COLUMNS


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess the healthcare performance DataFrame.

    1. Copies and standardizes column names.
    2. Standardizes 'district' as clean string.
    3. Parses and standardizes 'month' to 'YYYY-MM' strings while keeping chronological sort.
    4. Coerces numeric indicator columns to float.
    5. Deduplicates on (district, month) keeping the first occurrence.
    6. Sorts rows by district and chronological month.

    Returns:
        Clean, preprocessed pd.DataFrame.
    """
    clean_df = df.copy()
    clean_df.columns = [c.strip() for c in clean_df.columns]

    # Standardize District
    if "district" in clean_df.columns:
        clean_df["district"] = clean_df["district"].astype(str).str.strip()

    # Standardize Month
    if "month" in clean_df.columns:
        clean_df["month_raw"] = clean_df["month"].astype(str).str.strip()
        # Parse datetime to ensure proper chronological order
        parsed_dates = pd.to_datetime(clean_df["month_raw"], format="mixed", errors="coerce")
        clean_df["_sort_date"] = parsed_dates
        # Format as YYYY-MM if parse succeeded, else fallback to raw string
        clean_df["month"] = parsed_dates.dt.strftime("%Y-%m").fillna(clean_df["month_raw"])

    # Coerce Numeric columns
    numeric_cols = get_numeric_columns(clean_df)
    for col in numeric_cols:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    # Deduplicate by district and month if present
    if "district" in clean_df.columns and "month" in clean_df.columns:
        clean_df = clean_df.drop_duplicates(subset=["district", "month"])

    # Chronological sort
    if "_sort_date" in clean_df.columns and "district" in clean_df.columns:
        clean_df = clean_df.sort_values(by=["district", "_sort_date"]).reset_index(drop=True)
        clean_df = clean_df.drop(columns=["_sort_date", "month_raw"], errors="ignore")
    elif "district" in clean_df.columns and "month" in clean_df.columns:
        clean_df = clean_df.sort_values(by=["district", "month"]).reset_index(drop=True)

    return clean_df


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Identify all numeric indicator columns present in the dataset."""
    cols: List[str] = []
    for col in df.columns:
        if col in ["month", "district", "_sort_date", "month_raw"]:
            continue
        if col in DEFAULT_NUMERIC_COLUMNS or pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)
        else:
            # Check if majority of values are convertible to float
            coerced = pd.to_numeric(df[col], errors="coerce")
            if coerced.notna().sum() > 0:
                cols.append(col)
    return cols


def to_long_format(df: pd.DataFrame, numeric_cols: List[str] = None) -> pd.DataFrame:
    """Convert wide-format DataFrame to long tidy format (district, month, indicator, value)."""
    if numeric_cols is None:
        numeric_cols = get_numeric_columns(df)

    id_vars = [c for c in ["district", "month"] if c in df.columns]
    value_vars = [c for c in numeric_cols if c in df.columns]

    if not id_vars or not value_vars:
        return pd.DataFrame()

    long_df = pd.melt(
        df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="indicator",
        value_name="value",
    )
    return long_df.dropna(subset=["value"])
