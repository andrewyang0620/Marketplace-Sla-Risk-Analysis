# Data Validation & SLA Definition – Summary

- **Dataset coverage**
  - Total orders: **99,441**, customers: **99,441**, sellers: **3,088**.
  - The dataset covers orders from **2016-09-04** to **2018-10-17**, with no major gaps in monthly order volume.
  - Delivered orders account for **97.02%** of all orders.

- **Order–seller structure**
  - **98.7%** of orders involve a single seller.
  - Multi-seller orders are rare of **1.3%**, so assigning a primary seller per order is a reasonable simplification for seller-level SLA analysis.

- **SLA definition & delay behaviour**
  - SLA delay is defined as  
    `delay_days = delivered_customer_date - estimated_delivery_date`, computed only for orders with both timestamps present.
  - Among delivered orders, **6.57%** violate the promised delivery date (`delay_days > 0`).
  - **2.88%** of delivered orders experience **severe delay** (`delay_days > 7`), which will be used as “high customer harm” events in downstream analysis and simulations.
  - Extreme outliers (delay > 60 days): **79 orders (0.08%)** — retained but documented; do not materially affect aggregate SLA statistics.
  - `has_time_anomaly=True` flags orders where `delivered_date < purchased_date` (0 cases found); these would be excluded from SLA calculations if present.


- **Customer experience signal availability**
  - Among delivered orders, **99.33%** have a valid review score.
  - Review score distribution is J-shaped (1-star and 5-star dominate). Non-parametric tests (Mann-Whitney U) are preferred over mean comparisons in downstream CX analysis.
  - This provides a sufficiently large sample to study the relationship between SLA reliability, review scores, and repeat behaviour.

- **GMV coverage**
  - Order-level GMV is aggregated from the payments table and merged into `orders_sellers`.
  - Total platform GMV: **BRL 16,008,872**.
  - GMV at risk (orders with any SLA violation): **BRL 1,150,910 (7.19% of total GMV)**.

- **Data quality & joins**
  - `seller_id` is missing for only **0.78%** of orders, and these will be excluded from seller-level risk analysis.
  - No major structural issues were found in key joins between orders, items, sellers, reviews, and payments.
  - Basic sanity checks on delay distributions indicate realistic delivery times with only a small number of extreme outliers, which can be handled in later cleaning steps.

These checks confirm that the Olist dataset is structurally sound and suitable for:
1. Seller-level risk analysis,  
2. Customer impact validation, and  
3. GMV-at-risk quantification, and
4. ROI-oriented intervention simulation in subsequent notebooks.
