# A/B Testing Analysis

## Project Overview

This project evaluates the results of an A/B test designed to measure the impact of an experimental change on customer revenue and purchasing behavior.

The analysis combines data preparation, exploratory data analysis (EDA), experiment validation, statistical hypothesis testing, and business interpretation to determine whether the observed improvement is statistically significant and meets the experiment's success criteria.

## Business Objective

The primary objective is to determine whether the treatment group achieves **at least a 2% increase in revenue per assigned customer (RAC)** compared with the control group.

The analysis also evaluates guardrail metrics to ensure that the treatment does not negatively affect customer conversion or purchasing frequency.

### Success Criteria

- **Primary KPI:** Revenue per assigned customer must improve by at least 2%.
- **Guardrail metrics:** Conversion rate and orders per assigned customer must not deteriorate by more than 1%.
- **Statistical significance:** Hypothesis tests are conducted at a 5% significance level.

## Dataset

The project uses three datasets:

- `ab_assignment.csv`: Customer experiment assignments, including customer IDs, assigned groups, and assignment dates.
- `customer_profile.csv`: Customer profile and segmentation information.
- `customer_transactions.csv`: Customer purchasing activity, including orders, revenue, and items purchased.

## Methodology

### 1. Data Preparation

- Inspect dataset structure, data types, and missing values.
- Identify and handle duplicate customer assignments.
- Exclude customers assigned to both experimental groups.
- Merge assignment, profile, and transaction data.
- Apply appropriate missing-value treatments.
- Save intermediate and processed datasets for reproducibility.

### 2. Exploratory Data Analysis (EDA)

- Analyze customer characteristics and experiment group distributions.
- Examine missing values and data quality.
- Compare customer revenue, orders, and conversion behavior.
- Investigate differences across customer segments.
- Identify potential imbalances that could affect interpretation.

### 3. Experiment Validation

- Check the expected 50/50 allocation between control and treatment.
- Perform a Sample Ratio Mismatch (SRM) test.
- Investigate assignment imbalances across relevant customer segments.
- Assess potential limitations before interpreting treatment effects.

### 4. Statistical Hypothesis Testing

The primary KPI and guardrail metrics are evaluated using one-sided hypothesis tests aligned with the experiment's business requirements.

- **Primary KPI:** Test whether revenue per assigned customer improves by more than the 2% target.
- **Conversion rate:** Test whether the treatment remains within the permitted 1% deterioration margin.
- **Orders per assigned customer:** Test whether the treatment remains within the permitted 1% deterioration margin.

The analysis uses a significance level of \(\alpha = 0.05\), together with test statistics, p-values, and confidence bounds to support the final decision.

### 5. Business Recommendation

The final assessment considers statistical evidence, effect size, guardrail performance, and experiment validity before determining whether the treatment meets the business objectives.

## Project Structure

```text
DA_AB_Testing/
├── data/
│   ├── intermediate/
│   ├── processed/
│   └── raw/
├── docs/
├── notebooks/
├── reports/
├── src/
│   ├── ab_testing.py
│   ├── data_processing.py
│   └── main.py
├── requirements.txt
└── README.md
```

### Source Code

- **`ab_testing.py`**: Statistical hypothesis testing and experiment evaluation.
- **`data_processing.py`**: Data cleaning, preprocessing, and dataset preparation.
- **`main.py`**: Main entry point for executing the analysis.

### Other Directories

- **`data/raw/`**: Original input datasets.
- **`data/intermediate/`**: Intermediate datasets generated during data preparation.
- **`data/processed/`**: Cleaned datasets ready for analysis.
- **`notebooks/`**: Exploratory data analysis and supporting investigations.
- **`reports/`**: Analysis reports and visualizations.

## Installation

Clone the repository:

```bash
git clone https://github.com/Iban99/DA_AB_Testing.git
cd DA_AB_Testing
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Analysis

Execute the main analysis script from the project root:

```bash
python src/main.py
```

Ensure the required input datasets are available in the expected locations before running the analysis.


## Author

Developed as a data analytics project focused on experimentation, statistical inference, and data-driven decision-making.
