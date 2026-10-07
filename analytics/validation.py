"""Data Validation Module for Healthcare Performance CSV.

Validates uploaded datasets against the required schema, checks data types,
detects missing values, duplicates, and invalid date formats without crashing.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from utils.constants import REQUIRED_COLUMNS, DEFAULT_NUMERIC_COLUMNS


def validate_columns(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """Check whether all required columns are present in the DataFrame.

    Returns:
        (is_valid, missing_columns, extra_columns)
    """
    df_cols = [c.strip() for c in df.columns]
    missing = [col for col in REQUIRED_COLUMNS if col not in df_cols]
    extra = [col for col in df_cols if col not in REQUIRED_COLUMNS]
    return len(missing) == 0, missing, extra


def validate_data_types(df: pd.DataFrame) -> Tuple[bool, Dict[str, str], List[str]]:
    """Validate that expected numeric columns can be parsed as numbers.

    Returns:
        (is_valid, data_types_dict, non_numeric_errors)
    """
    dtypes_dict: Dict[str, str] = {}
    type_errors: List[str] = []

    for col in df.columns:
        dtypes_dict[col] = str(df[col].dtype)

    for col in DEFAULT_NUMERIC_COLUMNS:
        if col in df.columns:
            # Check if values can be converted to float
            coerced = pd.to_numeric(df[col], errors="coerce")
            nan_count = coerced.isna().sum()
            original_nan = df[col].isna().sum()
            new_nans = nan_count - original_nan
            if new_nans > 0:
                type_errors.append(
                    f"Column '{col}' contains {new_nans} non-numeric values."
                )

    return len(type_errors) == 0, dtypes_dict, type_errors


def validate_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Calculate missing/null values count per column."""
    return df.isna().sum().to_dict()


def validate_month(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Verify that 'month' values can be interpreted as valid dates or periods."""
    if "month" not in df.columns:
        return False, ["Missing 'month' column."]

    month_series = df["month"].dropna().astype(str).str.strip()
    if month_series.empty:
        return False, ["Month column is completely empty."]

    errors = []
    # Test datetime conversion
    try:
        parsed = pd.to_datetime(month_series, format="mixed", errors="coerce")
        invalid_count = parsed.isna().sum()
        if invalid_count > 0:
            errors.append(f"{invalid_count} values in 'month' could not be parsed as dates.")
    except Exception as e:
        errors.append(f"Failed to parse 'month' column dates: {str(e)}")

    return len(errors) == 0, errors


def validate_dataset(df: Any) -> Dict[str, Any]:
    """Perform comprehensive data validation on an uploaded DataFrame.

    Returns a structured dictionary containing validation status, errors,
    warnings, and dataset profiling statistics. Never raises an uncaught exception.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if df is None:
        return {
            "is_valid": False,
            "status": "Invalid",
            "errors": ["No dataset provided."],
            "warnings": [],
            "row_count": 0,
            "col_count": 0,
            "missing_counts": {},
            "duplicate_count": 0,
            "dtypes": {},
            "numeric_columns": [],
        }

    if not isinstance(df, pd.DataFrame):
        return {
            "is_valid": False,
            "status": "Invalid",
            "errors": ["Input data is not a valid Pandas DataFrame."],
            "warnings": [],
            "row_count": 0,
            "col_count": 0,
            "missing_counts": {},
            "duplicate_count": 0,
            "dtypes": {},
            "numeric_columns": [],
        }

    # 1. Empty dataset check
    row_count, col_count = df.shape
    if row_count == 0:
        errors.append("Uploaded dataset is empty (0 rows).")
        return {
            "is_valid": False,
            "status": "Invalid",
            "errors": errors,
            "warnings": warnings,
            "row_count": 0,
            "col_count": col_count,
            "missing_counts": {},
            "duplicate_count": 0,
            "dtypes": {},
            "numeric_columns": [],
        }

    # Normalize column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]

    # 2. Check required columns
    cols_ok, missing_cols, extra_cols = validate_columns(df)
    if not cols_ok:
        errors.append(
            f"Missing required columns: {', '.join(missing_cols)}. "
            f"Expected schema: {', '.join(REQUIRED_COLUMNS)}"
        )

    if extra_cols:
        warnings.append(
            f"Dataset contains additional non-standard columns: {', '.join(extra_cols)}."
        )

    # 3. Check data types
    types_ok, dtypes_dict, type_errors = validate_data_types(df)
    if not types_ok:
        errors.extend(type_errors)

    # 4. Check month column
    if "month" in df.columns:
        month_ok, month_errors = validate_month(df)
        if not month_ok:
            errors.extend(month_errors)

    # 5. Check duplicate rows
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        warnings.append(f"Found {duplicate_count} duplicate row(s). Duplicates will be handled.")

    # 6. Missing values
    missing_counts = validate_missing_values(df)
    total_missing = sum(missing_counts.values())
    if total_missing > 0:
        warnings.append(f"Found {total_missing} missing value(s) across {len([k for k, v in missing_counts.items() if v > 0])} column(s).")

    # 7. Check Granularity / History Recommendation
    if "district" in df.columns and "month" in df.columns and cols_ok:
        n_districts = df["district"].nunique()
        n_months = df["month"].nunique()
        if n_months < 2:
            warnings.append(
                f"Dataset contains only {n_months} month. At least 2 months are required for trend detection."
            )
        if n_districts < 5:
            warnings.append(
                f"Dataset contains only {n_districts} districts. Small district counts make Pearson correlation estimates statistically volatile."
            )

    # Detect available numeric columns
    numeric_columns = [
        c for c in df.columns
        if c in DEFAULT_NUMERIC_COLUMNS or pd.api.types.is_numeric_dtype(df[c])
    ]

    is_valid = len(errors) == 0
    status = "Valid" if is_valid and len(warnings) == 0 else ("Valid with Warnings" if is_valid else "Invalid")

    return {
        "is_valid": is_valid,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "row_count": row_count,
        "col_count": col_count,
        "missing_counts": missing_counts,
        "duplicate_count": duplicate_count,
        "dtypes": dtypes_dict,
        "numeric_columns": numeric_columns,
    }
