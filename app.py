"""Streamlit Application Entry Point.

Automated Healthcare Insight Engine
General-purpose district-level healthcare analytics and automated insight generation.

Architecture Principle:
All analytical, preprocessing, validation, and generation logic resides in the
'analytics/' package. This file handles presentation, user interaction, filtering,
and visualization.
"""

import io
import os
from typing import Dict, Any, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Modular analytics and utility imports
from analytics import (
    validate_dataset,
    preprocess_data,
    get_numeric_columns,
    detect_trends,
    trends_to_dataframe,
    detect_outliers,
    outliers_to_dataframe,
    compute_correlation_matrix,
    detect_significant_correlations,
    correlations_to_dataframe,
    generate_all_insights,
    insights_to_dataframe,
)
from utils.constants import (
    DEFAULT_TREND_THRESHOLD,
    DEFAULT_OUTLIER_METHOD,
    DEFAULT_ZSCORE_THRESHOLD,
    DEFAULT_CORRELATION_THRESHOLD,
    SEVERITY_COLORS,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)
from utils.helpers import get_indicator_label, get_indicator_unit, format_number


# ==============================================================================
# STREAMLIT PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Automated Healthcare Insight Engine",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom modern CSS for clean healthcare analytics styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .badge-high {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-medium {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #DBEAFE;
        color: #1D4ED8;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# DATA LOADING HELPERS
# ==============================================================================
@st.cache_data
def load_sample_data() -> pd.DataFrame:
    """Load default benchmark healthcare dataset."""
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_healthcare.csv")
    if os.path.exists(sample_path):
        return pd.read_csv(sample_path)
    # Fallback to inline benchmark dataframe if file missing
    data = {
        "month": ["2026-07", "2026-08", "2026-07", "2026-08", "2026-07", "2026-08",
                  "2026-07", "2026-08", "2026-07", "2026-08", "2026-07", "2026-08"],
        "district": ["Ahmedabad", "Ahmedabad", "Surat", "Surat", "Vadodara", "Vadodara",
                     "Rajkot", "Rajkot", "Mehsana", "Mehsana", "Bhavnagar", "Bhavnagar"],
        "anc_coverage": [85, 69, 81, 83, 90, 91, 79, 80, 84, 42, 77, 79],
        "institutional_delivery": [91, 90, 87, 89, 93, 94, 85, 86, 89, 88, 82, 84],
        "immunization": [93, 92, 91, 92, 96, 97, 89, 90, 92, 91, 87, 89],
        "high_risk_cases": [10, 13, 13, 12, 7, 6, 15, 14, 11, 28, 17, 15],
    }
    return pd.DataFrame(data)


def export_outputs(insights_df: pd.DataFrame, corr_df: pd.DataFrame):
    """Save latest analytical run outputs to outputs/ folder."""
    try:
        out_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(out_dir, exist_ok=True)
        insights_df.to_csv(os.path.join(out_dir, "insights.csv"), index=False)
        corr_df.to_csv(os.path.join(out_dir, "correlation_matrix.csv"))
    except Exception:
        pass


# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.title("Engine Controls")

# --- SECTION 1: DATA INGESTION ---
st.sidebar.header("📁 Data Source")
data_source = st.sidebar.radio(
    "Choose Data Source:",
    options=["Sample Benchmark Dataset", "Upload Custom CSV"],
    index=0,
)

raw_df: pd.DataFrame
if data_source == "Upload Custom CSV":
    uploaded_file = st.sidebar.file_uploader(
        "Upload District Performance CSV",
        type=["csv"],
        help="Upload CSV with month, district, and numerical healthcare metrics.",
    )
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file)
            st.sidebar.success(f"Loaded {len(raw_df)} rows from uploaded file.")
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")
            raw_df = pd.DataFrame()
    else:
        st.sidebar.info("Awaiting file upload. Using sample dataset temporarily.")
        raw_df = load_sample_data()
else:
    raw_df = load_sample_data()
    st.sidebar.info("Using standard sample dataset (6 districts, 2 months).")

# Validate Dataset Immediately
val_results = validate_dataset(raw_df)

if not val_results["is_valid"]:
    st.error("Uploaded CSV failed schema validation:")
    for err in val_results["errors"]:
        st.write(f"- ❌ {err}")
    st.stop()

# Preprocess DataFrame for downstream analytics
clean_df = preprocess_data(raw_df)
available_numeric_cols = get_numeric_columns(clean_df)
available_districts = sorted(clean_df["district"].dropna().unique().tolist())
available_months = sorted(clean_df["month"].dropna().unique().tolist())

# --- SECTION 2: LIVE FILTERS ---
st.sidebar.header("🔍 Filters")
selected_districts = st.sidebar.multiselect(
    "Filter Districts:",
    options=available_districts,
    default=available_districts,
)
selected_months = st.sidebar.multiselect(
    "Filter Months:",
    options=available_months,
    default=available_months,
)
selected_indicators = st.sidebar.multiselect(
    "Filter Indicators:",
    options=available_numeric_cols,
    default=available_numeric_cols,
    format_func=get_indicator_label,
)

# Apply filters
filtered_df = clean_df.copy()
if selected_districts:
    filtered_df = filtered_df[filtered_df["district"].isin(selected_districts)]
if selected_months:
    filtered_df = filtered_df[filtered_df["month"].isin(selected_months)]

# --- SECTION 3: ANALYTICS CONFIGURATION ---
st.sidebar.header("⚙️ Analytics Configuration")

trend_threshold = st.sidebar.slider(
    "Trend Threshold (±%):",
    min_value=5.0,
    max_value=50.0,
    value=DEFAULT_TREND_THRESHOLD,
    step=1.0,
    help="Period-over-period percentage change to flag as a significant trend.",
)

outlier_method = st.sidebar.selectbox(
    "Outlier Detection Method:",
    options=["IQR", "Z-Score"],
    index=0 if DEFAULT_OUTLIER_METHOD == "IQR" else 1,
    help="IQR uses Tukey Fences (Q1-1.5*IQR, Q3+1.5*IQR). Z-score uses standard deviation distance from mean.",
)

zscore_threshold = DEFAULT_ZSCORE_THRESHOLD
if outlier_method == "Z-Score":
    zscore_threshold = st.sidebar.slider(
        "Z-Score Threshold (σ):",
        min_value=2.0,
        max_value=5.0,
        value=DEFAULT_ZSCORE_THRESHOLD,
        step=0.1,
        help="Number of standard deviations from the mean to flag as an outlier.",
    )

correlation_threshold = st.sidebar.slider(
    "Correlation Threshold (|r|):",
    min_value=0.50,
    max_value=0.99,
    value=DEFAULT_CORRELATION_THRESHOLD,
    step=0.01,
    help="Absolute Pearson correlation coefficient threshold to flag significant co-movements.",
)


# ==============================================================================
# MAIN DASHBOARD HEADER
# ==============================================================================
st.markdown('<div class="main-header">Automated Healthcare Insight Engine</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">General-purpose district-level healthcare analytics and automated insight generation</div>',
    unsafe_allow_html=True,
)

# Run full dynamic analytics pipeline
active_indicators = selected_indicators if selected_indicators else available_numeric_cols
insights = generate_all_insights(
    df=filtered_df,
    trend_threshold_pct=trend_threshold,
    outlier_method=outlier_method,
    zscore_threshold=zscore_threshold,
    correlation_threshold=correlation_threshold,
)
insights_df = insights_to_dataframe(insights)

# Compute matrices & models
corr_matrix_df = compute_correlation_matrix(filtered_df, numeric_cols=active_indicators)
corr_pairs, corr_meta = detect_significant_correlations(
    filtered_df, threshold=correlation_threshold, numeric_cols=active_indicators
)
trend_records = detect_trends(filtered_df, threshold_pct=trend_threshold, numeric_cols=active_indicators)
outlier_records = detect_outliers(
    filtered_df, method=outlier_method, z_threshold=zscore_threshold, numeric_cols=active_indicators
)

# Sync outputs directory
export_outputs(insights_df, corr_matrix_df)


# ==============================================================================
# 1. DATA OVERVIEW
# ==============================================================================
st.subheader("1. Data Overview")
c1, c2, c3, c4, c5 = st.columns(5)

date_range_str = (
    f"{filtered_df['month'].min()} → {filtered_df['month'].max()}"
    if not filtered_df.empty and "month" in filtered_df.columns
    else "N/A"
)
total_missing = sum(val_results["missing_counts"].values())

with c1:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-title">Active Rows</div>
            <div class="metric-value">{len(filtered_df)} <span style="font-size:0.9rem;color:#64748B;">/ {val_results['row_count']}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-title">Districts</div>
            <div class="metric-value">{filtered_df['district'].nunique() if 'district' in filtered_df else 0}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-title">Indicators</div>
            <div class="metric-value">{len(active_indicators)}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-title">Date Range</div>
            <div class="metric-value" style="font-size:1.15rem;">{date_range_str}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c5:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-title">Missing Values</div>
            <div class="metric-value">{total_missing}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.write("")


# ==============================================================================
# 2. DATA VALIDATION REPORT
# ==============================================================================
with st.expander("2. Data Validation Report & Schema Inspection", expanded=False):
    status_color = "green" if val_results["is_valid"] and not val_results["warnings"] else "orange"
    st.markdown(f"**Dataset Validation Status:** :{status_color}[**{val_results['status']}**]")

    if val_results["warnings"]:
        for w in val_results["warnings"]:
            st.warning(f"⚠️ {w}")

    vc1, vc2 = st.columns(2)
    with vc1:
        st.markdown("**Column Schema & Missing Counts:**")
        schema_summary = []
        for col in val_results["dtypes"]:
            schema_summary.append({
                "Column": col,
                "Data Type": val_results["dtypes"][col],
                "Missing Values": val_results["missing_counts"].get(col, 0),
                "Category": "Metric" if col in val_results["numeric_columns"] else "Dimension",
            })
        st.dataframe(pd.DataFrame(schema_summary), use_container_width=True, hide_index=True)

    with vc2:
        st.markdown("**Raw Data Sample Preview:**")
        st.dataframe(raw_df.head(6), use_container_width=True, hide_index=True)


# ==============================================================================
# 3. AUTOMATED INSIGHTS
# ==============================================================================
st.subheader("3. Automated Human-Readable Insights")

if insights_df.empty:
    st.info("No significant insights detected under current filter thresholds.")
else:
    # Filter controls for insights
    ins_col1, ins_col2 = st.columns([1, 1])
    with ins_col1:
        type_filter = st.multiselect(
            "Filter by Insight Type:",
            options=sorted(insights_df["type"].unique()),
            default=sorted(insights_df["type"].unique()),
        )
    with ins_col2:
        severity_filter = st.multiselect(
            "Filter by Severity Level:",
            options=[SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW],
            default=[SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW],
        )

    filtered_insights_df = insights_df[
        insights_df["type"].isin(type_filter) & insights_df["severity"].isin(severity_filter)
    ]

    # Display Styled Cards for Top Insights
    st.markdown(f"**Displaying {len(filtered_insights_df)} Generated Insights:**")

    for _, row in filtered_insights_df.iterrows():
        sev = row["severity"]
        badge_class = f"badge-{sev.lower()}"
        icon = "🔴" if sev == "High" else ("🟡" if sev == "Medium" else "🔵")
        st.markdown(
            f"""
            <div style="background-color:white; border-left: 4px solid {'#EF4444' if sev=='High' else ('#F59E0B' if sev=='Medium' else '#3B82F6')};
                        padding: 12px 16px; margin-bottom: 10px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.06);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <div>
                        <span style="font-weight:700; color:#1E293B;">{row['insight_id']}</span> |
                        <span style="font-weight:600; text-transform:uppercase; color:#64748B; font-size:0.75rem;">{row['type']}</span> |
                        <span style="color:#0F172A; font-weight:500;">{row['entity']} ({row['indicator']})</span>
                    </div>
                    <div>
                        <span class="{badge_class}">{icon} {sev} Priority</span>
                    </div>
                </div>
                <div style="color:#334155; font-size:0.95rem; line-height:1.45;">
                    {row['explanation']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tabular View for verification & export inspection
    with st.expander("View Structured Insights Table (CSV Format)", expanded=False):
        st.dataframe(filtered_insights_df, use_container_width=True, hide_index=True)


# ==============================================================================
# 4. SEVERITY SUMMARY
# ==============================================================================
st.subheader("4. Severity Distribution")

sev_counts = {
    SEVERITY_HIGH: len(insights_df[insights_df["severity"] == SEVERITY_HIGH]),
    SEVERITY_MEDIUM: len(insights_df[insights_df["severity"] == SEVERITY_MEDIUM]),
    SEVERITY_LOW: len(insights_df[insights_df["severity"] == SEVERITY_LOW]),
}

sc1, sc2, sc3 = st.columns(3)
with sc1:
    st.markdown(
        f"""<div class="metric-card" style="border-left:4px solid #EF4444;">
            <div class="metric-title" style="color:#B91C1C;">High Severity Insights</div>
            <div class="metric-value" style="color:#B91C1C;">{sev_counts[SEVERITY_HIGH]}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with sc2:
    st.markdown(
        f"""<div class="metric-card" style="border-left:4px solid #F59E0B;">
            <div class="metric-title" style="color:#B45309;">Medium Severity Insights</div>
            <div class="metric-value" style="color:#B45309;">{sev_counts[SEVERITY_MEDIUM]}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with sc3:
    st.markdown(
        f"""<div class="metric-card" style="border-left:4px solid #3B82F6;">
            <div class="metric-title" style="color:#1D4ED8;">Low Severity Insights</div>
            <div class="metric-value" style="color:#1D4ED8;">{sev_counts[SEVERITY_LOW]}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.write("")

# Bar chart of Severity Breakdown by Insight Type
if not insights_df.empty:
    chart_df = insights_df.groupby(["type", "severity"]).size().reset_index(name="count")
    fig_sev = px.bar(
        chart_df,
        x="type",
        y="count",
        color="severity",
        color_discrete_map=SEVERITY_COLORS,
        barmode="group",
        title="Detected Findings by Type and Mathematical Severity Ranking",
        labels={"count": "Number of Insights", "type": "Finding Type", "severity": "Severity"},
    )
    fig_sev.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    st.plotly_chart(fig_sev, use_container_width=True)


# ==============================================================================
# 5. TREND ANALYSIS
# ==============================================================================
st.subheader("5. Period-Over-Period Trend Analysis")

t_col1, t_col2 = st.columns([1, 1])
with t_col1:
    chart_district = st.selectbox(
        "Select District for Longitudinal Trajectory:",
        options=available_districts,
        index=0 if available_districts else 0,
    )
with t_col2:
    chart_indicator = st.selectbox(
        "Select Indicator:",
        options=active_indicators,
        index=0 if active_indicators else 0,
        format_func=get_indicator_label,
    )

# Render Line Chart
if chart_district and chart_indicator and not filtered_df.empty:
    district_data = filtered_df[filtered_df["district"] == chart_district].sort_values("month")
    unit = get_indicator_unit(chart_indicator)
    label = get_indicator_label(chart_indicator)

    fig_line = px.line(
        district_data,
        x="month",
        y=chart_indicator,
        markers=True,
        title=f"{chart_district} — {label} Over Time",
        labels={"month": "Month", chart_indicator: f"{label} ({unit})"},
    )
    fig_line.update_traces(
        line=dict(color="#4F46E5", width=3),
        marker=dict(size=8, color="#312E81"),
    )
    fig_line.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    st.plotly_chart(fig_line, use_container_width=True)

# Significant Trends Table
trends_df = trends_to_dataframe(trend_records)
significant_trends_df = trends_df[trends_df["is_significant"] == True]

st.markdown(f"**Significant Trends Flagged (|change| ≥ {trend_threshold:.0f}%):**")
if significant_trends_df.empty:
    st.info("No significant trends crossed the configured threshold.")
else:
    display_trends = significant_trends_df.copy()
    display_trends["change_pct"] = display_trends["change_pct"].apply(lambda x: f"{x:+.1f}%")
    st.dataframe(
        display_trends[
            ["district", "indicator", "previous_period", "current_period", "previous_value", "current_value", "change_pct", "direction"]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# 6. OUTLIER ANALYSIS
# ==============================================================================
st.subheader("6. Statistical Outlier Detection")

outliers_df = outliers_to_dataframe(outlier_records)

oc1, oc2 = st.columns([1, 2])
with oc1:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-title">Outliers Identified ({outlier_method})</div>
            <div class="metric-value">{len(outliers_df)}</div>
            <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">
                {'Tukey Fences: [Q1 - 1.5*IQR, Q3 + 1.5*IQR]' if outlier_method == 'IQR' else f'Z-Score Threshold: ±{zscore_threshold}σ'}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with oc2:
    if not filtered_df.empty and active_indicators:
        # Boxplot across all active indicators
        long_df = pd.melt(
            filtered_df,
            id_vars=["district", "month"],
            value_vars=active_indicators,
            var_name="indicator",
            value_name="value",
        )
        long_df["indicator_label"] = long_df["indicator"].apply(get_indicator_label)
        fig_box = px.box(
            long_df,
            x="indicator_label",
            y="value",
            points="all",
            title=f"Indicator Distributions & Data Points Across Districts",
            color="indicator_label",
        )
        fig_box.update_layout(
            template="plotly_white",
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_box, use_container_width=True)

if outliers_df.empty:
    st.info(f"No statistical outliers detected under the current {outlier_method} parameters.")
else:
    st.markdown("**Detected Outlier Observations:**")
    st.dataframe(outliers_df, use_container_width=True, hide_index=True)


# ==============================================================================
# 7. CORRELATION ANALYSIS
# ==============================================================================
st.subheader("7. Correlation Matrix & Linear Associations")

# Statistical limitation callout required by rubric
if corr_meta.get("warning"):
    st.warning(f"⚠️ **Statistical Caveat:** {corr_meta['warning']}")
else:
    st.info("ℹ️ Correlation reflects linear co-movement and does not imply direct medical causation.")

heat_col, pairs_col = st.columns([1.2, 1])

with heat_col:
    if not corr_matrix_df.empty:
        # Heatmap
        clean_matrix_labels = [get_indicator_label(c) for c in corr_matrix_df.columns]
        fig_heat = px.imshow(
            corr_matrix_df.values,
            x=clean_matrix_labels,
            y=clean_matrix_labels,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            text_auto=".2f",
            title="Pearson Correlation Heatmap",
        )
        fig_heat.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

with pairs_col:
    st.markdown(f"**Significant Correlated Indicator Pairs (|r| ≥ {correlation_threshold:.2f}):**")
    if not corr_pairs:
        st.info("No indicator pairs exceeded the configured correlation threshold.")
    else:
        corr_pairs_df = correlations_to_dataframe(corr_pairs)
        st.dataframe(
            corr_pairs_df[["indicator_1", "indicator_2", "correlation", "relationship", "p_value"]],
            use_container_width=True,
            hide_index=True,
        )


# ==============================================================================
# 8. CSV EXPORTS & DOWNLOADS
# ==============================================================================
st.subheader("8. Export Analytical Outputs")
st.markdown("Download auto-generated insights and correlation matrices formatted according to specification.")

d1, d2 = st.columns(2)

with d1:
    insights_csv_buffer = io.StringIO()
    insights_df.to_csv(insights_csv_buffer, index=False)
    st.download_button(
        label="📥 Download Insights CSV (insights.csv)",
        data=insights_csv_buffer.getvalue(),
        file_name="insights.csv",
        mime="text/csv",
        use_container_width=True,
    )

with d2:
    corr_csv_buffer = io.StringIO()
    corr_matrix_df.to_csv(corr_csv_buffer)
    st.download_button(
        label="📥 Download Correlation Matrix CSV (correlation_matrix.csv)",
        data=corr_csv_buffer.getvalue(),
        file_name="correlation_matrix.csv",
        mime="text/csv",
        use_container_width=True,
    )
