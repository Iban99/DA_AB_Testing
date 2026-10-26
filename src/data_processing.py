"""
A/B test — data preparation and descriptive metrics.

Expected input files:
    data/raw/ab_assignment.csv
    data/raw/customer_profile.csv
    data/raw/transactions.csv

Output:
    data/processed/full_data.parquet

"""

# Import Libraries
from pathlib import Path
import profile
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from scipy.stats import chisquare


# -------------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
INTERMEDIATE_DIR = PROJECT_DIR / "data" / "intermediate"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# Raw data
ASSIGNMENT_FILE_RAW = RAW_DIR / "ab_assignment.csv"
PROFILE_FILE_RAW = RAW_DIR / "customer_profile.csv"
TRANSACTIONS_FILE_RAW = RAW_DIR / "transactions.csv"

# Intermediate data
ASSIGNMENT_FILE_INTERMEDIATE = INTERMEDIATE_DIR / "ab_assignment.parquet"
PROFILE_FILE_INTERMEDIATE = INTERMEDIATE_DIR / "customer_profile.parquet"
TRANSACTIONS_FILE_INTERMEDIATE = INTERMEDIATE_DIR / "transactions.parquet"

# Processed data
OUTPUT_FILE = PROCESSED_DIR / "full_data.parquet"

# Variables/Constants
EXPERIMENT_START = pd.Timestamp("2026-02-01")
EXPERIMENT_END = pd.Timestamp("2026-03-01")


# -------------------------------------------------------------------------------------
# Data ingestion
# -------------------------------------------------------------------------------------
def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the three source datasets."""
    paths = [ASSIGNMENT_FILE_RAW, PROFILE_FILE_RAW, TRANSACTIONS_FILE_RAW]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "The following input file(s) could not be found:\n- "
            + "\n- ".join(missing)
            + "\nCheck the project folder structure and file names."
        )

    assignment = pd.read_csv(ASSIGNMENT_FILE_RAW)
    cust_profile = pd.read_csv(PROFILE_FILE_RAW)
    transactions = pd.read_csv(TRANSACTIONS_FILE_RAW)

    return assignment, cust_profile, transactions


def validate_columns(
    assignment: pd.DataFrame,
    cust_profile: pd.DataFrame,
    transactions: pd.DataFrame,
) -> None:
    """Fail early if a source dataset does not have the expected columns."""
    expected = {
        "assignment": {
            "customer_id", "group", "assignment_date"
        },
        "profile": {
            "customer_id", "historical_value_segment", "gender",
            "age", "region", "registration_date"
        },
        "transactions": {
            "order_id", "customer_id", "order_date", "revenue", "items"
        },
    }
    actual = {
        "assignment": set(assignment.columns),
        "profile": set(cust_profile.columns),
        "transactions": set(transactions.columns),
    }

    errors = []
    for dataset_name, required in expected.items():
        missing = required - actual[dataset_name]
        if missing:
            errors.append(f"{dataset_name}: missing columns {sorted(missing)}")

    if errors:
        raise ValueError("Invalid input schema:\n- " + "\n- ".join(errors))


# -------------------------------------------------------------------------------------
# Assignment cleaning and SRM diagnostic
# -------------------------------------------------------------------------------------
def clean_assignment(assignment: pd.DataFrame) -> pd.DataFrame:
    """
    Remove exact duplicate rows, then exclude customers assigned to
    more than one experimental group.

    Customers assigned to both groups are excluded from both groups, as
    documented in the EDA. The remaining sample is not downsampled to 50/50.
    """
    assignment = assignment.copy()

    if assignment["customer_id"].isna().any():
        raise ValueError("Assignment data contains null customer_id values.")

    assignment["assignment_date"] = pd.to_datetime(
        assignment["assignment_date"], dayfirst=True, errors="raise"
    )

    # Remove exact duplicates
    rows_before = len(assignment)
    assignment = assignment.drop_duplicates().copy()
    exact_duplicates_removed = rows_before - len(assignment)

    # Remove customers assigned to multiple groups
    groups_per_customer = assignment.groupby("customer_id")["group"].nunique()
    multi_group_ids = groups_per_customer[groups_per_customer > 1].index
    multi_group_customers = len(multi_group_ids)

    assignment = assignment[
        ~assignment["customer_id"].isin(multi_group_ids)
    ].copy()

    # Check whether duplicate customers still exist
    if assignment["customer_id"].duplicated().any():
        raise ValueError(
            "Duplicate customers still exist. The process cannot continue."
        )

    # Ensure that only 'control' and 'test' groups exist
    groups = set(assignment["group"].dropna().unique())
    if groups != {"control", "test"}:
        raise ValueError(
            "Expected assignment groups 'control' and 'test'; "
            f"found {sorted(groups)}."
        )

    print("\nASSIGNMENT DATA QUALITY")
    print(f"Exact duplicate rows removed: {exact_duplicates_removed:,}")
    print(
        "Customers assigned to multiple groups and excluded: "
        f"{multi_group_customers:,}"
    )
    print(f"Rows after cleaning: {len(assignment):,}")
    print("\nCustomers per group after cleaning:")
    print(
        assignment.groupby("group")["customer_id"]
        .nunique()
        .reindex(["control", "test"])
        .to_string()
    )

    return assignment


def report_srm(assignment: pd.DataFrame) -> None:
    """
    Report the chi-square Sample Ratio Mismatch diagnostic against a 50/50
    allocation. This is a warning to investigate, not a reason to resample.
    """

    customers = (
        assignment.groupby("group")["customer_id"]
        .nunique()
        .reindex(["control", "test"])
    )
    total_customers = int(customers.sum())
    expected = [total_customers / 2, total_customers / 2]
    result = chisquare(f_obs=customers.to_numpy(), f_exp=expected)

    print("\nSAMPLE RATIO MISMATCH (SRM)")
    print(f"Observed customers: {customers.to_dict()}")
    print(f"Expected customers under 50/50: {[round(x, 1) for x in expected]}")
    print(f"Chi-square statistic: {result.statistic:.4f}")
    print(f"p-value: {result.pvalue:.6g}")

    if result.pvalue < 0.05:
        print(
            "WARNING: significant SRM at alpha = 0.05. Investigate the "
            "assignment and data pipeline before interpreting the result "
            "causally. Do not correct this by post-hoc resampling."
        )


# ---------------------------------------------------------------------
# Customer profile cleaning
# ---------------------------------------------------------------------
def clean_profile(profile: pd.DataFrame) -> pd.DataFrame:
    """Parse registration date and impute missing age with the median."""
    profile = profile.copy()

    # Verify that customer_id is not null and unique
    if profile["customer_id"].isna().any():
        raise ValueError("Customer profile contains null customer_id values.")

    if profile["customer_id"].duplicated().any():
        duplicate_count = int(profile["customer_id"].duplicated().sum())
        raise ValueError(
            f"Customer profile contains {duplicate_count} duplicate customer_id "
            "rows. Investigate these before merging."
        )

    # Ensure that registration_date is datetime type
    profile["registration_date"] = pd.to_datetime(
        profile["registration_date"], errors="raise"
    )

    missing_age = int(profile["age"].isna().sum())
    median_age = profile["age"].median()
    if pd.isna(median_age):
        raise ValueError("Cannot impute age because all age values are missing.")

    # This follows the EDA decision: no age outlier treatment; missing age
    # values are imputed with the median, then stored as integers.
    profile["age"] = profile["age"].fillna(median_age).astype(int)

    print("\nCUSTOMER PROFILE")
    print(f"Missing age values imputed with median ({median_age:.1f}): {missing_age:,}")

    return profile


# ---------------------------------------------------------------------
# Transaction preparation and cleaning
# ---------------------------------------------------------------------
def clean_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """Filter transactions to the experiment period"""
    transactions = transactions.copy()

    # Verify that customer_id and order_id are not null
    if transactions["customer_id"].isna().any():
        raise ValueError("Transactions contain null customer_id values.")
    if transactions["order_id"].isna().any():
        raise ValueError("Transactions contain null order_id values.")

    # Ensure order_date is datetime type
    transactions["order_date"] = pd.to_datetime(
        transactions["order_date"], errors="raise"
    )

    # Filter transactions to the experiment period
    transactions = transactions.loc[
        (transactions["order_date"] >= EXPERIMENT_START)
        & (transactions["order_date"] < EXPERIMENT_END)
    ].copy()

    print("\nTRANSACTIONS")
    print(
        "Experiment window: "
        f"{EXPERIMENT_START.date()} to "
        f"{(EXPERIMENT_END - pd.Timedelta(days=1)).date()}"
    )
    print(f"Transaction rows in window: {len(transactions):,}")

    return transactions


# ---------------------------------------------------------------------
# Build the analysis dataset
# ---------------------------------------------------------------------
def build_analysis_dataset(
    assignment: pd.DataFrame,
    cust_profile: pd.DataFrame,
    transactions: pd.DataFrame,
) -> pd.DataFrame:

    # Merge assignment with customer profile.
    data = pd.merge(
        assignment,
        cust_profile,
        on="customer_id",
        how="left"
    )

    # Transactions are order-level aggregates, so first ensure they are aggregated at the customer level.
    transactions = transactions.groupby("customer_id").agg(
        total_orders = ("order_id", "count"),
        total_revenue = ("revenue", "sum"),
        min_revenue = ("revenue", "min"),
        max_revenue = ("revenue", "max"),
        avg_revenue = ("revenue", "mean"),
        total_items = ("items", "sum"),
        avg_items = ("items", "mean"),
        min_order_date = ("order_date", "min"),
        max_order_date = ("order_date", "max")).reset_index().copy()

    # Merge the aggregated transaction data with the main dataset.
    data = data.merge(
        transactions,
        left_on="customer_id",
        right_on="customer_id",
        how="left"
    )

    # A customer is converted if they placed at least one order during the
    # experiment. Keep this definition consistent with the EDA/metric design.
    data["is_active"] = (data["total_orders"] > 0).astype(int)

    # Fill missing values for total items, total revenue, and total orders with 0
    data[["total_items", "total_revenue", "total_orders"]] = data[["total_items", "total_revenue", "total_orders"]].fillna(0)

    # Final integrity checks.
    if data["customer_id"].duplicated().any():
        raise ValueError("Final analysis dataset contains duplicated customers.")

    return data


# ---------------------------------------------------------------------
# Summary of descriptive metrics
# ---------------------------------------------------------------------
def calculate_group_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate the primary KPI, guardrails and supporting diagnostics."""
    group_metrics = data.groupby("group").agg(
        customers=("customer_id", "nunique"),
        total_revenue=("total_revenue", "sum"),
        total_orders=("total_orders", "sum"),
        total_items=("total_items", "sum"),
        active_customers=("is_active", "sum"),
        rac_kpi=("total_revenue", "mean"), # Revenue per assigned customer (RAC) KPI
        median_revenue=("total_revenue", "median"),
        mean_revenue=("total_revenue", "mean"),
        revenue_std=("total_revenue", "std")
    )
    # Guardrail conversion rate
    group_metrics["conversion_rate"] = group_metrics["active_customers"] / group_metrics["customers"]
    # Orders per assigned customer (OPAC)
    group_metrics["opac"] = group_metrics["total_orders"] / group_metrics["customers"]

    group_metrics["items_per_order"] = (
        group_metrics["total_items"] / group_metrics["total_orders"].replace(0, np.nan)
    )

    return group_metrics


# ---------------------------------------------------------------------
# Summary of descriptive metrics of historical segments
# ---------------------------------------------------------------------
def calculate_segment_diagnostics(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate descriptive metrics and representation by historical segment."""
    diagnostics = data.groupby(
        ["group", "historical_value_segment"], dropna=False
    ).agg(
        customers=("customer_id", "nunique"),
        total_revenue=("total_revenue", "sum"),
        total_orders=("total_orders", "sum"),
        total_items=("total_items", "sum"),
        mean_revenue=("total_revenue", "mean"),
        median_revenue=("total_revenue", "median"),
        revenue_std=("total_revenue", "std"),
    )

    diagnostics["rac"] = diagnostics["total_revenue"] / diagnostics["customers"]
    diagnostics["opac"] = diagnostics["total_orders"] / diagnostics["customers"]
    diagnostics["rev_x_order"] = (
        diagnostics["total_revenue"] / diagnostics["total_orders"].replace(0, np.nan)
    )
    diagnostics["items_per_order"] = (
        diagnostics["total_items"] / diagnostics["total_orders"].replace(0, np.nan)
    )

    group_sizes = data.groupby("group")["customer_id"].nunique()
    denominators = diagnostics.index.get_level_values("group").map(group_sizes)
    diagnostics["representation_pct"] = diagnostics["customers"] / denominators * 100

    return diagnostics

# ---------------------------------------------------------------------
# Main data processing pipeline
# ---------------------------------------------------------------------
def main_processing() -> pd.DataFrame:
    """
    Execute the complete data preparation pipeline.
    Returns:
        pd.DataFrame: Final customer-level analysis dataset.
    """
    print("\n" + "=" * 70)
    print("STARTING DATA PROCESSING PIPELINE")
    print("=" * 70)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Load the raw datasets.
    assignment, cust_profile, transactions = load_raw_data()

    print("\nRAW DATA LOADED")
    print(f'Assignment info: {assignment.info()}')
    print(f'Customer profile info: {cust_profile.info()}')
    print(f'Transactions info: {transactions.info()}')

    # Validate the input schemas.
    validate_columns(assignment, cust_profile, transactions)

    # Clean the assignment dataset.
    assignment = clean_assignment(assignment)

    # Diagnose the sample ratio mismatch without rebalancing.
    report_srm(assignment)

    # Clean the customer profile dataset.
    cust_profile = clean_profile(cust_profile)

    # Prepare transactions for the experiment period.
    transactions = clean_transactions(transactions)

    # Save the intermediate datasets.
    assignment.to_parquet(
        ASSIGNMENT_FILE_INTERMEDIATE,
        index=False,
    )

    cust_profile.to_parquet(
        PROFILE_FILE_INTERMEDIATE,
        index=False,
    )

    transactions.to_parquet(
        TRANSACTIONS_FILE_INTERMEDIATE,
        index=False,
    )

    print("\nINTERMEDIATE DATASETS SAVED")
    print(f"Assignment: {ASSIGNMENT_FILE_INTERMEDIATE}")
    print(f"Customer profile: {PROFILE_FILE_INTERMEDIATE}")
    print(f"Transactions: {TRANSACTIONS_FILE_INTERMEDIATE}")

    # Build the final customer-level analysis dataset.
    full_data = build_analysis_dataset(
        assignment=assignment,
        cust_profile=cust_profile,
        transactions=transactions,
    )

    # Validate the final dataset.
    if full_data["customer_id"].isna().any():
        raise ValueError(
            "The final dataset contains null customer_id values. "
            "The process cannot continue."
        )

    if full_data["customer_id"].duplicated().any():
        raise ValueError(
            "Duplicate customers still exist in the final dataset. "
            "The process cannot continue."
        )

    # Save the final dataset.
    full_data.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print("\nFINAL DATASET SAVED")
    print(f"Path: {OUTPUT_FILE}")
    print(f"Rows: {len(full_data):,}")
    print(f"Columns: {len(full_data.columns):,}")

    # Display descriptive metrics.
    group_metrics = calculate_group_metrics(full_data)
    segment_diagnostics = calculate_segment_diagnostics(full_data)

    print("\nDESCRIPTIVE METRICS BY GROUP")
    print(group_metrics.to_string())

    print("\nDESCRIPTIVE METRICS BY HISTORICAL SEGMENT")
    print(segment_diagnostics.to_string())

    print("\n" + "=" * 70)
    print("DATA PROCESSING COMPLETED SUCCESSFULLY")
    print("=" * 70)

    return full_data, group_metrics, segment_diagnostics