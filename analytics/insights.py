"""Automated Insight Generation Engine.

Converts structured mathematical results from trend detection, outlier analysis,
and correlation metrics into dynamic, human-readable insight narratives.
Ensures zero hardcoded entities or narrative values.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from utils.constants import (
    INSIGHT_TYPE_TREND,
    INSIGHT_TYPE_OUTLIER,
    INSIGHT_TYPE_CORRELATION,
    INSIGHT_TYPE_THRESHOLD_BREACH,
    DEFAULT_TREND_THRESHOLD,
    DEFAULT_OUTLIER_METHOD,
    DEFAULT_ZSCORE_THRESHOLD,
    DEFAULT_CORRELATION_THRESHOLD,
)
from utils.helpers import get_indicator_label, get_indicator_unit, format_number, format_percentage
from analytics.trends import detect_trends, filter_significant_trends
from analytics.outliers import detect_outliers
from analytics.correlations import detect_significant_correlations
from analytics.severity import (
    calculate_trend_severity,
    calculate_iqr_outlier_severity,
    calculate_zscore_outlier_severity,
    calculate_correlation_severity,
)


@dataclass
class Insight:
    """Structured container for an automated analytical insight."""
    insight_id: str
    type: str
    indicator: str
    entity: str
    period: str
    value: Any
    prev_value: Any
    change_pct: Any
    severity: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_trend_insights(
    trend_records: List[Dict[str, Any]],
    threshold_pct: float = DEFAULT_TREND_THRESHOLD,
    start_id: int = 1,
) -> Tuple[List[Insight], int]:
    """Dynamically generate human-readable insights for significant trends."""
    insights: List[Insight] = []
    current_id = start_id

    significant_trends = filter_significant_trends(trend_records)

    for item in significant_trends:
        district = item["district"]
        indicator = item["indicator"]
        label = get_indicator_label(indicator)
        unit = get_indicator_unit(indicator)
        direction = item["direction"]
        prev_period = item["previous_period"]
        curr_period = item["current_period"]
        prev_val = item["previous_value"]
        curr_val = item["current_value"]
        change_pct = item["change_pct"]
        abs_change = abs(change_pct)

        severity = calculate_trend_severity(change_pct, threshold_pct)

        unit_str = f"{unit}" if unit else ""
        explanation = (
            f"{district}'s {label} {direction} by {abs_change:.1f}% from {prev_period} "
            f"to {curr_period} ({prev_val}{unit_str} → {curr_val}{unit_str}), "
            f"exceeding the configured {threshold_pct:.0f}% significant-change threshold."
        )

        insights.append(
            Insight(
                insight_id=f"INS-{current_id:04d}",
                type=INSIGHT_TYPE_TREND,
                indicator=indicator,
                entity=district,
                period=curr_period,
                value=curr_val,
                prev_value=prev_val,
                change_pct=change_pct,
                severity=severity,
                explanation=explanation,
            )
        )
        current_id += 1

    return insights, current_id


def generate_outlier_insights(
    outlier_records: List[Dict[str, Any]],
    start_id: int = 1,
) -> Tuple[List[Insight], int]:
    """Dynamically generate human-readable insights for statistical outliers."""
    insights: List[Insight] = []
    current_id = start_id

    for item in outlier_records:
        district = item["district"]
        indicator = item["indicator"]
        label = get_indicator_label(indicator)
        unit = get_indicator_unit(indicator)
        month = item["month"]
        val = item["value"]
        method = item["method"]

        unit_str = f"{unit}" if unit else ""

        if method == "IQR":
            distance = item["distance_from_bound"]
            iqr = item["iqr"]
            lower_bound = item["lower_bound"]
            upper_bound = item["upper_bound"]
            median = item["median"]
            severity = calculate_iqr_outlier_severity(distance, iqr)

            bound_desc = (
                f"below lower fence of {lower_bound}{unit_str}"
                if item["bound_breached"] == "below_lower"
                else f"above upper fence of {upper_bound}{unit_str}"
            )

            # Calculate deviation percentage from median for change metric
            change_metric = round(((val - median) / median * 100.0), 1) if median != 0 else None

            explanation = (
                f"{district}'s {label} recorded {val}{unit_str} in {month}, "
                f"which is an anomalous outlier {bound_desc} "
                f"(distribution median: {median}{unit_str}, IQR: {iqr}{unit_str})."
            )
            prev_val = median
        else:
            # Z-Score method
            z = item["z_score"]
            mean = item["mean"]
            std = item["std"]
            thresh = item["threshold"]
            severity = calculate_zscore_outlier_severity(z, thresh)

            direction = "below" if z < 0 else "above"
            change_metric = round(((val - mean) / mean * 100.0), 1) if mean != 0 else None

            explanation = (
                f"{district}'s {label} recorded {val}{unit_str} in {month}, "
                f"deviating by {abs(z):.1f}σ {direction} the state mean of {mean}{unit_str} "
                f"(configured threshold: ±{thresh:.1f}σ, standard deviation: {std}{unit_str})."
            )
            prev_val = mean

        insights.append(
            Insight(
                insight_id=f"INS-{current_id:04d}",
                type=INSIGHT_TYPE_OUTLIER,
                indicator=indicator,
                entity=district,
                period=month,
                value=val,
                prev_value=prev_val,
                change_pct=change_metric,
                severity=severity,
                explanation=explanation,
            )
        )
        current_id += 1

    return insights, current_id


def generate_correlation_insights(
    corr_pairs: List[Dict[str, Any]],
    period_label: str = "All Observed Periods",
    start_id: int = 1,
) -> Tuple[List[Insight], int]:
    """Dynamically generate human-readable insights for strong correlations."""
    insights: List[Insight] = []
    current_id = start_id

    for item in corr_pairs:
        col1 = item["indicator_1"]
        col2 = item["indicator_2"]
        label1 = get_indicator_label(col1)
        label2 = get_indicator_label(col2)
        r = item["correlation"]
        abs_r = item["absolute_correlation"]
        relationship = item["relationship"]
        p_val = item.get("p_value")
        n_samples = item.get("sample_size", 0)

        severity = calculate_correlation_severity(abs_r)

        p_str = f", p = {p_val:.4f}" if p_val is not None else ""
        explanation = (
            f"{label1} and {label2} show a strong {relationship} linear Pearson "
            f"correlation of {r:+.2f}{p_str} across districts (n = {n_samples}). "
            f"Note: correlation reflects co-movement and does not imply direct causation."
        )

        insights.append(
            Insight(
                insight_id=f"INS-{current_id:04d}",
                type=INSIGHT_TYPE_CORRELATION,
                indicator=f"{col1}:{col2}",
                entity="Statewide",
                period=period_label,
                value=r,
                prev_value="n/a",
                change_pct="n/a",
                severity=severity,
                explanation=explanation,
            )
        )
        current_id += 1

    return insights, current_id


def generate_all_insights(
    df: pd.DataFrame,
    trend_threshold_pct: float = DEFAULT_TREND_THRESHOLD,
    outlier_method: str = DEFAULT_OUTLIER_METHOD,
    zscore_threshold: float = DEFAULT_ZSCORE_THRESHOLD,
    correlation_threshold: float = DEFAULT_CORRELATION_THRESHOLD,
) -> List[Insight]:
    """Execute end-to-end analytical pipeline and aggregate all dynamic insights.

    Args:
        df: Clean, preprocessed DataFrame.
        trend_threshold_pct: Percentage change threshold for trends.
        outlier_method: 'IQR' or 'Z-Score'.
        zscore_threshold: Standard deviations threshold.
        correlation_threshold: Pearson r threshold.

    Returns:
        Consolidated list of structured Insight instances.
    """
    if df.empty:
        return []

    # 1. Trend detection
    trends = detect_trends(df, threshold_pct=trend_threshold_pct)
    trend_insights, next_id = generate_trend_insights(
        trends, threshold_pct=trend_threshold_pct, start_id=1
    )

    # 2. Outlier detection
    outliers = detect_outliers(
        df, method=outlier_method, z_threshold=zscore_threshold
    )
    outlier_insights, next_id = generate_outlier_insights(
        outliers, start_id=next_id
    )

    # 3. Correlation detection
    period_str = "All Periods"
    if "month" in df.columns:
        months_sorted = sorted(df["month"].dropna().unique())
        if len(months_sorted) > 1:
            period_str = f"{months_sorted[0]}..{months_sorted[-1]}"
        elif len(months_sorted) == 1:
            period_str = str(months_sorted[0])

    corr_pairs, _ = detect_significant_correlations(
        df, threshold=correlation_threshold
    )
    corr_insights, next_id = generate_correlation_insights(
        corr_pairs, period_label=period_str, start_id=next_id
    )

    all_insights = trend_insights + outlier_insights + corr_insights
    return all_insights


def insights_to_dataframe(insights: List[Insight]) -> pd.DataFrame:
    """Convert a list of Insight objects into the standardized CSV DataFrame format.

    Columns match the required assignment specification:
        insight_id, type, indicator, entity, period, value, prev_value, change_pct, severity, explanation
    """
    if not insights:
        return pd.DataFrame(
            columns=[
                "insight_id",
                "type",
                "indicator",
                "entity",
                "period",
                "value",
                "prev_value",
                "change_pct",
                "severity",
                "explanation",
            ]
        )

    records = [i.to_dict() for i in insights]
    return pd.DataFrame(records)
