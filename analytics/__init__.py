"""Analytics Package for Automated Insight Generation.

Exposes validation, preprocessing, statistical trend detection,
outlier detection, correlation analysis, severity ranking, and insight generation.
"""

from analytics.validation import (
    validate_dataset,
    validate_columns,
    validate_data_types,
    validate_missing_values,
    validate_month,
)
from analytics.preprocessing import (
    preprocess_data,
    get_numeric_columns,
    to_long_format,
)
from analytics.trends import (
    detect_trends,
    filter_significant_trends,
    trends_to_dataframe,
)
from analytics.outliers import (
    detect_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
    outliers_to_dataframe,
)
from analytics.correlations import (
    compute_correlation_matrix,
    detect_significant_correlations,
    correlations_to_dataframe,
)
from analytics.severity import (
    calculate_trend_severity,
    calculate_iqr_outlier_severity,
    calculate_zscore_outlier_severity,
    calculate_correlation_severity,
)
from analytics.insights import (
    Insight,
    generate_all_insights,
    generate_trend_insights,
    generate_outlier_insights,
    generate_correlation_insights,
    insights_to_dataframe,
)

__all__ = [
    "validate_dataset",
    "validate_columns",
    "validate_data_types",
    "validate_missing_values",
    "validate_month",
    "preprocess_data",
    "get_numeric_columns",
    "to_long_format",
    "detect_trends",
    "filter_significant_trends",
    "trends_to_dataframe",
    "detect_outliers",
    "detect_outliers_iqr",
    "detect_outliers_zscore",
    "outliers_to_dataframe",
    "compute_correlation_matrix",
    "detect_significant_correlations",
    "correlations_to_dataframe",
    "calculate_trend_severity",
    "calculate_iqr_outlier_severity",
    "calculate_zscore_outlier_severity",
    "calculate_correlation_severity",
    "Insight",
    "generate_all_insights",
    "generate_trend_insights",
    "generate_outlier_insights",
    "generate_correlation_insights",
    "insights_to_dataframe",
]
