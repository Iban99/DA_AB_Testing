# Orquestrin A/B Testing Pipeline
# This script orchestrates the end-to-end A/B testing workflow, including data processing,
# calculation of descriptive metrics, and execution of statistical tests.

from data_processing import main_processing
from ab_testing import main_ab_testing


def main():
    # Explain metodology 
    print("\n" + "=" * 70)
    print("SUMMARY OF THE METHODOLOGIES USED")
    print("=" * 70)

    print("""\nProject Methodology:
        1. Objective & Experimental Design
        2. Data Cleaning & Preparation
        3. Exploratory Data Analysis (EDA) 
        4. Sample Ratio Mismatch (SRM) & Randomization Checks
        5. Primary KPI: Revenue per Assigned Customer
        6. Guardrail Metrics: Conversion Rate & Orders per Assigned Customer
        7. Segment & Sensitivity Analysis
        8. Results Interpretation & Business Recommendation
        9. Reproducibility & Final Deliverable""")
    print("-" * 70)
    print("""\nHypothesis Testing Methodology:
        - Define the Business Objective: Establish the target uplift and acceptable guardrail deterioration.
        - Formulate the Hypotheses: Define the null and alternative hypotheses for the primary KPI and guardrail metrics.
        - Select the Statistical Tests: Choose the appropriate tests based on metric type, distributional assumptions and non-inferiority requirements.
        - Set the Significance Level: Define the significance threshold (alpha = 0.05) and testing direction.
        - Calculate Test Statistics and P-values: Run the selected tests and quantify the statistical evidence.
        - Interpret the Results: Evaluate the primary KPI against the 2% uplift threshold and guardrails against the 1% non-inferiority margins.
        - Draw the Business Conclusion: Determine whether the evidence supports rollout, considering the SRM issue and other experimental limitations.""")
    
    # Step 1: Process data and calculate descriptive metrics
    data, group_metrics, segment_diagnostics = main_processing()

    # Step 2: Run A/B testing
    main_ab_testing(data, group_metrics, segment_diagnostics)


if __name__ == "__main__":
    main()