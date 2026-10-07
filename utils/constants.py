"""Constants for the Automated Insight Generation Engine.

This module centralizes configuration constants, default thresholds,
column mappings, and insight categories to ensure maintainability
and consistency across the analytical pipeline.
"""

from typing import List, Dict

# Required CSV Columns for Healthcare Performance Dataset
REQUIRED_COLUMNS: List[str] = [
    "month",
    "district",
    "anc_coverage",
    "institutional_delivery",
    "immunization",
    "high_risk_cases",
]

# Primary numerical healthcare indicators to analyze
DEFAULT_NUMERIC_COLUMNS: List[str] = [
    "anc_coverage",
    "institutional_delivery",
    "immunization",
    "high_risk_cases",
]

# Human-readable labels for indicators
INDICATOR_DISPLAY_NAMES: Dict[str, str] = {
    "anc_coverage": "Antenatal Care (ANC) Coverage",
    "institutional_delivery": "Institutional Delivery",
    "immunization": "Immunization Coverage",
    "high_risk_cases": "High-Risk Pregnancy Cases",
}

# Indicator units of measurement
INDICATOR_UNITS: Dict[str, str] = {
    "anc_coverage": "%",
    "institutional_delivery": "%",
    "immunization": "%",
    "high_risk_cases": "cases",
}

# Analytical Default Thresholds
DEFAULT_TREND_THRESHOLD: float = 10.0  # Percentage change threshold (e.g. 10%)
DEFAULT_OUTLIER_METHOD: str = "IQR"   # "IQR" or "Z-Score"
DEFAULT_ZSCORE_THRESHOLD: float = 3.0  # Standard deviations
DEFAULT_CORRELATION_THRESHOLD: float = 0.70  # Pearson correlation coefficient threshold

# Insight Types
INSIGHT_TYPE_TREND: str = "trend"
INSIGHT_TYPE_OUTLIER: str = "outlier"
INSIGHT_TYPE_CORRELATION: str = "correlation"
INSIGHT_TYPE_THRESHOLD_BREACH: str = "threshold_breach"

VALID_INSIGHT_TYPES: List[str] = [
    INSIGHT_TYPE_TREND,
    INSIGHT_TYPE_OUTLIER,
    INSIGHT_TYPE_CORRELATION,
    INSIGHT_TYPE_THRESHOLD_BREACH,
]

# Severity Levels
SEVERITY_LOW: str = "Low"
SEVERITY_MEDIUM: str = "Medium"
SEVERITY_HIGH: str = "High"

VALID_SEVERITY_LEVELS: List[str] = [
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
]

# Color mappings for visualizations
SEVERITY_COLORS: Dict[str, str] = {
    SEVERITY_LOW: "#3B82F6",      # Blue
    SEVERITY_MEDIUM: "#F59E0B",   # Amber
    SEVERITY_HIGH: "#EF4444",     # Red
}

TYPE_COLORS: Dict[str, str] = {
    INSIGHT_TYPE_TREND: "#6366F1",
    INSIGHT_TYPE_OUTLIER: "#EC4899",
    INSIGHT_TYPE_CORRELATION: "#10B981",
    INSIGHT_TYPE_THRESHOLD_BREACH: "#F97316",
}
