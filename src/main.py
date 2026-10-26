# Orquestrin A/B Testing Pipeline
# This script orchestrates the end-to-end A/B testing workflow, including data processing,
# calculation of descriptive metrics, and execution of statistical tests.

from data_processing import main_processing
from ab_testing import main_ab_testing


def main():
    # Step 1: Process data and calculate descriptive metrics
    data, group_metrics, segment_diagnostics = main_processing()

    # Step 2: Run A/B testing
    main_ab_testing(data, group_metrics, segment_diagnostics)


if __name__ == "__main__":
    main()