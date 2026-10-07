"""Comprehensive Automated Test Suite for Analytics Engine.

Tests data validation, preprocessing, trend detection, outlier methods,
correlation analysis, severity classification, and dynamic insight generation.
"""

import os
import unittest
import pandas as pd
import numpy as np

from analytics.validation import validate_dataset
from analytics.preprocessing import preprocess_data, get_numeric_columns
from analytics.trends import detect_trends, filter_significant_trends
from analytics.outliers import detect_outliers_iqr, detect_outliers_zscore
from analytics.correlations import compute_correlation_matrix, detect_significant_correlations
from analytics.severity import (
    calculate_trend_severity,
    calculate_iqr_outlier_severity,
    calculate_zscore_outlier_severity,
    calculate_correlation_severity,
)
from analytics.insights import generate_all_insights, insights_to_dataframe


class TestAnalyticsEngine(unittest.TestCase):

    def setUp(self):
        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_healthcare.csv")
        self.raw_df = pd.read_csv(sample_path)
        self.clean_df = preprocess_data(self.raw_df)

    def test_validation_valid_dataset(self):
        report = validate_dataset(self.raw_df)
        self.assertTrue(report["is_valid"])
        self.assertEqual(report["row_count"], 12)
        self.assertEqual(report["col_count"], 6)
        self.assertEqual(sum(report["missing_counts"].values()), 0)

    def test_validation_missing_columns(self):
        invalid_df = pd.DataFrame({"month": ["2026-07"], "district": ["Test"]})
        report = validate_dataset(invalid_df)
        self.assertFalse(report["is_valid"])
        self.assertTrue(any("Missing required columns" in err for err in report["errors"]))

    def test_validation_empty_dataset(self):
        empty_df = pd.DataFrame()
        report = validate_dataset(empty_df)
        self.assertFalse(report["is_valid"])
        self.assertTrue(any("empty" in err for err in report["errors"]))

    def test_preprocessing_sorting_and_types(self):
        self.assertEqual(len(self.clean_df), 12)
        self.assertTrue(pd.api.types.is_numeric_dtype(self.clean_df["anc_coverage"]))
        numeric_cols = get_numeric_columns(self.clean_df)
        self.assertIn("anc_coverage", numeric_cols)
        self.assertIn("high_risk_cases", numeric_cols)

    def test_trend_detection(self):
        trends = detect_trends(self.clean_df, threshold_pct=10.0)
        self.assertGreater(len(trends), 0)
        sig_trends = filter_significant_trends(trends)
        
        # Verify Ahmedabad ANC dropped by ~18.82%
        ahmedabad_anc = [
            t for t in sig_trends
            if t["district"] == "Ahmedabad" and t["indicator"] == "anc_coverage"
        ]
        self.assertEqual(len(ahmedabad_anc), 1)
        self.assertAlmostEqual(ahmedabad_anc[0]["change_pct"], -18.82, places=1)
        self.assertEqual(ahmedabad_anc[0]["direction"], "decreased")
        self.assertTrue(ahmedabad_anc[0]["is_significant"])

        # Verify Mehsana high risk cases jumped by 154.55%
        mehsana_hrc = [
            t for t in sig_trends
            if t["district"] == "Mehsana" and t["indicator"] == "high_risk_cases"
        ]
        self.assertEqual(len(mehsana_hrc), 1)
        self.assertAlmostEqual(mehsana_hrc[0]["change_pct"], 154.55, places=1)

    def test_iqr_outlier_detection(self):
        outliers = detect_outliers_iqr(self.clean_df)
        self.assertGreater(len(outliers), 0)
        
        # Check Mehsana ANC (42.0) is identified as below lower bound
        mehsana_anc_outlier = [
            o for o in outliers
            if o["district"] == "Mehsana" and o["indicator"] == "anc_coverage"
        ]
        self.assertEqual(len(mehsana_anc_outlier), 1)
        self.assertEqual(mehsana_anc_outlier[0]["value"], 42.0)
        self.assertEqual(mehsana_anc_outlier[0]["bound_breached"], "below_lower")

    def test_zscore_outlier_detection(self):
        outliers = detect_outliers_zscore(self.clean_df, threshold=2.0)
        self.assertGreater(len(outliers), 0)
        for o in outliers:
            self.assertGreaterEqual(abs(o["z_score"]), 2.0)

    def test_correlation_detection(self):
        corr_matrix = compute_correlation_matrix(self.clean_df)
        self.assertEqual(corr_matrix.shape, (4, 4))
        self.assertAlmostEqual(corr_matrix.loc["anc_coverage", "anc_coverage"], 1.0)

        pairs, meta = detect_significant_correlations(self.clean_df, threshold=0.70)
        self.assertGreater(len(pairs), 0)
        # Check that warning for small dataset is present
        self.assertIsNotNone(meta.get("warning"))

    def test_severity_calculation(self):
        # Trend severity
        self.assertEqual(calculate_trend_severity(12.0, threshold_pct=10.0), "Low")
        self.assertEqual(calculate_trend_severity(20.0, threshold_pct=10.0), "Medium")
        self.assertEqual(calculate_trend_severity(35.0, threshold_pct=10.0), "High")

        # Correlation severity
        self.assertEqual(calculate_correlation_severity(0.75), "Low")
        self.assertEqual(calculate_correlation_severity(0.85), "Medium")
        self.assertEqual(calculate_correlation_severity(0.95), "High")

    def test_insights_generation_schema(self):
        insights = generate_all_insights(self.clean_df)
        self.assertGreater(len(insights), 0)
        df_out = insights_to_dataframe(insights)

        required_output_cols = [
            "insight_id", "type", "indicator", "entity", "period",
            "value", "prev_value", "change_pct", "severity", "explanation"
        ]
        for col in required_output_cols:
            self.assertIn(col, df_out.columns)

        # Check that insight IDs start with INS-
        for i_id in df_out["insight_id"]:
            self.assertTrue(i_id.startswith("INS-"))

        # Verify no null explanations
        self.assertTrue(df_out["explanation"].notna().all())


if __name__ == "__main__":
    unittest.main()
