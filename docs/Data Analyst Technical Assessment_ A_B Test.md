# Data Analyst Technical Assessment: A/B Test Analysis

## Business context

A new customer experience was tested to determine whether it increases customer spending without negatively affecting purchasing behaviour.

Customers were expected to be randomly assigned in equal proportions to:

* `control`: existing customer experience.
* `test`: new customer experience.

The experiment ran from **1 February 2026 to 28 February 2026**, inclusive.

The datasets may contain records outside the experiment period. These records represent historical customer activity and may be used when relevant. Only activity occurring during the dates above should be considered part of the experiment outcome.

## Available datasets

### `ab_assignment.csv`

Contains the assignment of customers to the experiment.

* `customer_id`: customer identifier.
* `group`: assigned experiment group.
* `assignment_date`: assignment date.

### `customer_profile.csv`

Contains customer characteristics and historical segmentation information.

* `customer_id`: customer identifier.
* `historical_value_segment`: historical customer-value segment.
* `gender`: customer gender.
* `age`: customer age.
* `region`: customer region.
* `registration_date`: registration date.

### `transactions.csv`

Contains one row per recorded order.

* `order_id`: order identifier.
* `customer_id`: customer identifier.
* `order_date`: transaction date.
* `revenue`: total order revenue in euros.
* `items`: number of items in the order.

Customers without transactions do not appear in this dataset.

## Business metrics

### Primary KPI

**Revenue per assigned customer**

$$
\frac{\text{Total revenue during the experiment}}
{\text{Number of customers assigned to the group}}
$$

The business would consider an improvement of at least **2% relative uplift** commercially relevant.

### Guardrail metrics

The new experience should not materially reduce:

* **Conversion rate:** percentage of assigned customers who placed at least one order during the experiment.
* **Orders per assigned customer:** number of orders divided by the number of assigned customers.

A relative deterioration greater than **1%** in either guardrail should be highlighted.

### Diagnostic metrics

You may use additional metrics when they help explain the result, such as:

* Average order value.
* Items per order.
* Customer-level revenue distribution.
* Results by customer characteristics or over time.

These metrics are diagnostic and should not replace the primary KPI when making the final recommendation.

## Questions to answer

1. Did the Test experience achieve its business objective?
2. What is the estimated impact on the primary KPI and guardrail metrics?
3. How confident are you in the result?
4. Are there any data-quality or experiment-design considerations that affect your interpretation?
5. Would you recommend rolling out the new experience? Explain your reasoning and propose the next steps.

Your analysis should lead to a clear business recommendation:

* **Roll out**
* **Do not roll out**
* **Inconclusive / further investigation required**

## Expected deliverables

Please provide:

* The code or queries used to perform the analysis.
* A concise report or presentation of no more than **two slides/pages**.
* A clear explanation of your methodology, assumptions and final recommendation.

You may use Python.

The assessment is designed to take approximately **three hours**.However, you are not expected to complete every part within that time.

The exercise is intentionally broad, as we want to evaluate different aspects of your analytical approach. We value analytical judgement, clarity, prioritisation and reasoning more than speed or the number of analyses or visualisations produced.

Use of AI tools is allowed, but it should be disclosed. You should be able to explain and defend every part of the submitted analysis.
