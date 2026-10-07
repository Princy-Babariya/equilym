"""Helper utilities for formatting and general data operations."""

from typing import Any, Union
from utils.constants import INDICATOR_DISPLAY_NAMES, INDICATOR_UNITS


def format_number(val: Any, decimals: int = 1) -> str:
    """Safely format a numerical value with given decimals."""
    if val is None:
        return "N/A"
    try:
        val_float = float(val)
        if val_float.is_integer():
            return f"{int(val_float)}"
        return f"{val_float:.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)


def format_percentage(val: Any, decimals: int = 1, show_sign: bool = True) -> str:
    """Format a number as a percentage string with optional +/- sign."""
    if val is None:
        return "N/A"
    try:
        val_float = float(val)
        sign = "+" if show_sign and val_float > 0 else ""
        return f"{sign}{val_float:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(val)


def get_indicator_label(col: str) -> str:
    """Return human-friendly indicator label."""
    return INDICATOR_DISPLAY_NAMES.get(col, col.replace("_", " ").title())


def get_indicator_unit(col: str) -> str:
    """Return unit of indicator."""
    return INDICATOR_UNITS.get(col, "")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on zero or NaN division."""
    try:
        if denominator == 0 or denominator is None or numerator is None:
            return default
        return numerator / denominator
    except Exception:
        return default
