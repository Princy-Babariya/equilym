# Automated Insight Generation Engine

An automated, general-purpose analytics engine that ingests district-level healthcare performance datasets and autonomously identifies longitudinal trends, statistical outliers, indicator correlations, and translates them into human-readable, data-driven narrative insights.

---

## 1. Problem Statement

Public health administrators and district program officers regularly monitor monthly key performance indicators (KPIs) such as Antenatal Care (ANC) coverage, institutional deliveries, immunization rates, and high-risk pregnancy counts. However:
- Manual inspection of tabular CSVs is time-consuming and error-prone.
- Subtle yet critical multi-district shifts (e.g., sudden drop in ANC or surge in high-risk pregnancies) can go unnoticed until aggregated statewide reports are finalized months later.
- Non-technical decision-makers need clear narrative insights ("*what happened, where, by how much, and why it matters*") rather than raw tables.

This project delivers a **general-purpose automated insight generation system** that programmatically computes mathematical deviations and synthesizes structured narrative reports without hardcoding any district-specific logic or narrative strings.

---

## 2. Solution Overview

The system processes raw district-level healthcare data through a modular analytical pipeline:
1. **Schema Validation & Profiling**: Guarantees column presence, data types, and temporal formats before computation.
2. **Deterministic Preprocessing**: Cleans dates, standardizes district names, coerces floats, and enforces chronological ordering.
3. **Multi-Method Statistical Analytics**:
   - **Period-Over-Period Trend Detection**: Computes relative percentage changes over time per district.
   - **Statistical Outlier Detection**: Identifies anomalies using Tukey's Interquartile Range (IQR) fences or parametric Z-scores.
   - **Bivariate Correlation Analysis**: Evaluates linear co-movement using Pearson correlation coefficients and p-values.
4. **Dynamic Insight Generation**: Populates sentence templates exclusively with mathematically calculated values, entities, and periods.
5. **Data-Derived Severity Classification**: Assigns `Low`, `Medium`, or `High` priority based on continuous ratio benchmarks against configurable user thresholds.
6. **Interactive Streamlit Dashboard**: Provides filtering, exploratory visual analytics (line trajectories, box distributions, correlation heatmaps), and exports formatted CSV outputs.

---

## 3. Architecture

```
                       ┌──────────────────────────────┐
                       │   District Performance CSV   │
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │    Data Validation Layer     │ (validation.py)
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │     Preprocessing Layer      │ (preprocessing.py)
                       └──────────────┬───────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
       ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
       │ Trend Detection │   │Outlier Detection│   │  Correlations   │
       │   (trends.py)   │   │  (outliers.py)  │   │(correlations.py)│
       └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
                │                     │                     │
                └─────────────────────┼─────────────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │  Severity Classification     │ (severity.py)
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │   Dynamic Insight Engine     │ (insights.py)
                       └──────────────┬───────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                ▼                                           ▼
       ┌─────────────────┐                         ┌─────────────────┐
       │Streamlit Web App│                         │   CSV Exports   │
       │    (app.py)     │                         │   (outputs/)    │
       └─────────────────┘                         └─────────────────┘
```

---

## 4. Technology Stack

- **Python 3.10+**: Core programming language.
- **Pandas**: Tabular manipulation, schema validation, rolling time-series calculations, and correlation matrices.
- **NumPy**: Vectorized numerical operations, quantile computations, and standard deviations.
- **SciPy (stats)**: Statistical hypothesis testing, exact p-values for Pearson correlations.
- **Streamlit**: Lightweight, reactive Python user interface and dashboard engine.
- **Plotly Express & Graph Objects**: Interactive, responsive data visualizations (line charts, boxplots, correlation heatmaps).

---

## 5. Project Structure

```
automated-insight-generation/
│
├── app.py                      # Streamlit dashboard interface & interactive visualization controller
│
├── analytics/                  # Core data science and statistical analytics package
│   ├── __init__.py             # Package exports for clean public API
│   ├── validation.py           # Schema, type, null, and duplicate checks
│   ├── preprocessing.py        # Date standardisation, sorting, and type coercion
│   ├── trends.py               # Period-over-period percentage change calculations
│   ├── outliers.py             # Tukey IQR fences and standard Z-score anomaly detectors
│   ├── correlations.py         # Pearson correlation matrix & bivariate pair filtering
│   ├── severity.py             # Objective mathematical Low/Medium/High severity logic
│   └── insights.py             # Dynamic templated sentence generation and dataclass models
│
├── utils/                      # Shared helper constants and formatting routines
│   ├── __init__.py             # Utils package initialization
│   ├── constants.py            # System thresholds, column definitions, and UI palettes
│   └── helpers.py              # Number formatting, safe division, and label mappers
│
├── data/
│   └── sample_healthcare.csv   # Benchmark district healthcare dataset (6 districts, 2 months)
│
├── outputs/
│   ├── insights.csv            # Auto-generated structured insights output
│   └── correlation_matrix.csv  # Computed Pearson correlation matrix output
│
├── requirements.txt            # Minimal pip dependencies
├── README.md                   # Comprehensive architectural and interview documentation
├── .gitignore                  # Git exclusions for artifacts and environments
└── run_streamlit.sh            # Production runner script
```

---

## 6. Data Flow

1. **Ingestion**: The user selects either the bundled benchmark dataset or uploads a custom CSV file.
2. **Validation**: `validation.py` inspects the DataFrame for the required schema (`month`, `district`, `anc_coverage`, `institutional_delivery`, `immunization`, `high_risk_cases`), counts missing fields, checks for duplicate rows, and validates date formats.
3. **Preprocessing**: `preprocessing.py` standardizes column whitespace, parses dates into ISO `YYYY-MM` while tracking true chronological ordering, coerces indicator columns to numeric types, and sorts rows by `(district, month)`.
4. **Statistical Execution**:
   - `trends.py` groups observations by district and computes period-over-period delta percentages.
   - `outliers.py` computes state/dataset-wide distribution statistics (quartiles, IQR, bounds, mean, standard deviation) and flags boundary breaches.
   - `correlations.py` evaluates pairwise linear correlation coefficients and flags pairs where $|r| \ge \text{threshold}$.
5. **Severity Determination**: `severity.py` calculates relative ratios against configured thresholds to objectively categorize each finding as `Low`, `Medium`, or `High`.
6. **Insight Synthesis**: `insights.py` populates structured dataclasses (`Insight`) with precise dynamic values and human-readable sentences.
7. **Presentation & Export**: `app.py` renders interactive metric cards, filterable insight cards, charts, and enables one-click CSV downloads.

---

## 7. Trend Detection Formula

For each `(district, indicator)` pair sorted chronologically:

$$\Delta\% = \left( \frac{V_{\text{current}} - V_{\text{previous}}}{V_{\text{previous}}} \right) \times 100$$

A trend is flagged as significant when:

$$|\Delta\%| \ge \text{Trend Threshold} \quad (\text{Default: } 10\%)$$

### Edge Case Handling:
- If $V_{\text{previous}} = 0$ and $V_{\text{current}} = 0$: $\Delta\% = 0.0\%$.
- If $V_{\text{previous}} = 0$ and $V_{\text{current}} > 0$: $\Delta\% = +100.0\%$.
- Null/NaN values in either period are skipped gracefully to prevent skewed calculations.

---

## 8. Outlier Detection Formulas

### A. Interquartile Range (IQR) Method (Tukey's Fences)
For each indicator distribution across the dataset:

$$Q_1 = 25\text{th percentile}, \quad Q_3 = 75\text{th percentile}$$
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Lower Bound} = Q_1 - 1.5 \times \text{IQR}$$
$$\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$

An observation is flagged as an outlier if:

$$V < \text{Lower Bound} \quad \lor \quad V > \text{Upper Bound}$$

### B. Parametric Z-Score Method
For each indicator:

$$\mu = \text{Mean}, \quad \sigma = \text{Standard Deviation (sample, } \text{ddof}=1\text{)}$$
$$z = \frac{V - \mu}{\sigma}$$

An observation is flagged if:

$$|z| \ge \text{Z-Score Threshold} \quad (\text{Default: } 3.0\sigma)$$

---

## 9. Correlation Detection

Pairwise Pearson correlation coefficient between indicators $X$ and $Y$:

$$r = \frac{\sum (X_i - \bar{X})(Y_i - \bar{Y})}{\sqrt{\sum (X_i - \bar{X})^2 \sum (Y_i - \bar{Y})^2}}$$

Pairs are flagged when:

$$|r| \ge \text{Correlation Threshold} \quad (\text{Default: } 0.70)$$

Exact two-tailed $p$-values are computed via `scipy.stats.pearsonr`.

---

## 10. Insight Generation Architecture

Rather than hardcoding sentences, the engine uses **structured data containers** that fill templated grammar with dynamically computed values:

```python
@dataclass
class Insight:
    insight_id: str      # e.g., "INS-0001"
    type: str            # "trend", "outlier", "correlation"
    indicator: str       # Indicator key name
    entity: str          # District name or "Statewide"
    period: str          # Observation period(s)
    value: Any           # Metric value
    prev_value: Any      # Benchmark or previous value
    change_pct: Any      # Percentage change or deviation
    severity: str        # "Low", "Medium", "High"
    explanation: str     # Data-driven narrative sentence
```

### Dynamic Sentence Construction:
- **Trend**:
  `"{entity}'s {indicator_label} {direction} by {abs_change}% from {prev_period} to {curr_period} ({prev_val} → {curr_val}), exceeding the configured {threshold}% significant-change threshold."`
- **IQR Outlier**:
  `"{entity}'s {indicator_label} recorded {val} in {month}, which is an anomalous outlier {below lower / above upper} fence of {bound} (distribution median: {median}, IQR: {iqr})."`
- **Correlation**:
  `"{indicator_1} and {indicator_2} show a strong {positive/negative} linear Pearson correlation of {r} (p = {p_value}) across districts (n = {n}). Note: correlation reflects co-movement and does not imply direct causation."`

---

## 11. Severity Logic

Severity is **never hardcoded** using arbitrary magic numbers. Instead, it is computed mathematically based on how far an observation deviates relative to user-configured thresholds:

### Trend Severity:
$$\text{Relative Ratio} = \frac{|\Delta\%|}{\text{Trend Threshold}}$$

| Severity | Mathematical Condition | Interpretation |
| :--- | :--- | :--- |
| **Low** | $\text{Ratio} < 1.5$ | Modest breach of threshold ($1.0\times$ to $1.5\times$) |
| **Medium** | $1.5 \le \text{Ratio} < 2.5$ | Moderate breach ($1.5\times$ to $2.5\times$) |
| **High** | $\text{Ratio} \ge 2.5$ | Severe breach ($\ge 2.5\times$ the significant threshold) |

### Outlier Severity (IQR):
$$\text{Excess Ratio} = \frac{|\text{Distance Beyond Fence}|}{\text{IQR}}$$

| Severity | Condition | Interpretation |
| :--- | :--- | :--- |
| **Low** | $\text{Ratio} < 0.5$ | Marginally beyond Tukey fence |
| **Medium** | $0.5 \le \text{Ratio} < 1.0$ | Distinct anomaly |
| **High** | $\text{Ratio} \ge 1.0$ | Severe anomaly ($\ge 1$ full IQR outside fence) |

### Correlation Severity:
| Severity | Absolute $|r|$ Range |
| :--- | :--- |
| **Low** | $0.70 \le |r| < 0.80$ |
| **Medium** | $0.80 \le |r| < 0.90$ |
| **High** | $|r| \ge 0.90$ |

---

## 12. User Interface Configuration Controls

All analytical parameters can be adjusted in real time via sidebar sliders:
- **Trend Threshold**: Range $5\% - 50\%$ (Default: $10\%$).
- **Outlier Method**: Toggle between `IQR` and `Z-Score`.
- **Z-Score Threshold**: Range $2.0\sigma - 5.0\sigma$ (Default: $3.0\sigma$).
- **Correlation Threshold**: Range $0.50 - 0.99$ (Default: $0.70$).
- **Multi-Dimensional Filters**: Live multiselect controls for districts, months, and indicators.

---

## 13. Running the Project

### Prerequisites:
Python 3.10 or higher.

### Installation:
```bash
# 1. Clone repository or navigate to project directory
cd automated-insight-generation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Streamlit dashboard
streamlit run app.py
```

The web dashboard will open automatically in your browser at `http://localhost:8501` (or port 3000 in containerized environments).

---

## 14. Sample Dataset & Expected Dynamic Findings

The bundled benchmark dataset (`data/sample_healthcare.csv`) contains:
- **6 Districts**: Ahmedabad, Surat, Vadodara, Rajkot, Mehsana, Bhavnagar.
- **2 Time Periods**: 2026-07 and 2026-08 (12 total records).
- **4 Indicators**: `anc_coverage`, `institutional_delivery`, `immunization`, `high_risk_cases`.

### Key Discoveries Computed Dynamically:
1. **Ahmedabad ANC Coverage**: Drops from $85\%$ to $69\%$ ($-18.82\%$, flagged as Medium Trend and Outlier).
2. **Mehsana ANC Coverage**: Plummets from $84\%$ to $42\%$ ($-50.0\%$, flagged as High Trend and extreme Outlier).
3. **Mehsana High-Risk Cases**: Spikes from $11$ to $28$ ($+154.55\%$, flagged as High Trend and extreme Outlier).
4. **Strong Negative Correlation**: `anc_coverage` vs `high_risk_cases` ($r = -0.9335, p < 0.001$).
5. **Strong Positive Correlation**: `institutional_delivery` vs `immunization` ($r = +0.9786, p < 0.001$).

---

## 15. Limitations & Caveats

1. **Small Sample Volatility**: With 2 months $\times$ 6 districts ($n = 12$ rows), Pearson correlation estimates are sensitive to single-point leverage (such as Mehsana's dual anomaly). The UI prominently warns users of this statistical fragility.
2. **Correlation $\neq$ Causation**: High correlation between `institutional_delivery` and `immunization` indicates shared systemic capacity or concurrent outreach, not direct causal dependency.
3. **Trend Granularity**: Longitudinal trend detection requires at least 2 consecutive periods per district. Datasets with only 1 period will produce outlier and correlation insights but cannot compute delta trends.

---

## 16. How to Explain This Project in an Interview

When presenting this project to interviewers:

1. **Start with the Core Mandate**:
   > *"The assignment required a general-purpose, automated healthcare analytics engine that transforms district CSVs into dynamic human-readable insights without hardcoded narratives."*

2. **Highlight Architectural Decoupling**:
   > *"I strictly separated concerns: `app.py` handles presentation and filtering, while all statistical logic lives in dedicated modules inside `analytics/` (`validation.py`, `trends.py`, `outliers.py`, `correlations.py`, `severity.py`, `insights.py`)."*

3. **Demonstrate Data-Driven Dynamics**:
   > *"Not a single district name or percentage is hardcoded. If you upload a dataset with 50 districts in California or Kenya, the engine parses the schema, computes IQR bounds and period changes, ranks severity mathematically, and synthesizes tailored sentences."*

4. **Address Severity & Statistics Openly**:
   > *"Rather than arbitrary if-statements like `if change > 50`, severity is normalized against the user's configured threshold ratio ($\Delta\% / \text{Threshold}$). I also surfaced small-sample correlation cautions because good data science requires honesty about statistical sample size limitations."*
