
## Seller Risk Analysis – Summary

- **Analysis scope & data quality**
  - Total orders: **99,441**, spanning from **2016-09-04** to **2018-10-17** (25 months).
  - Analysis window: Last **180 days** (ending 2018-10-17), covering **2,021 sellers** with at least 1 delivered order.
  - No duplicate (order_id, seller_id) pairs detected; SLA violation fields have **0% missing rate** for delivered orders.
  - Long-tail distribution: 86% of sellers have ≤10 orders in the analysis window.

- **Risk concentration (H1 validation)**
  - After filtering for sellers with ≥10 delivered orders: **588 sellers** analyzed.
  - **Top 10% sellers** (59 sellers) contribute:
    - **37.15%** of all SLA violations
    - **39.16%** of severity-weighted violations
  - **H1 confirmed**: SLA risk is highly concentrated, validating the need for targeted seller intervention.

- **Risk tier segmentation (180-day window)**
  - **High risk** (24 sellers, 4.1%): 
    - Mean violation rate: **10.2%**
    - Minimum delivered orders: 50
    - Contribute **25.4%** of total violations despite small population
  - **Medium risk** (104 sellers, 17.7%): 
    - Mean violation rate: **5.7%**
    - Minimum delivered orders: 20
    - Contribute **41.7%** of violations
  - **Low risk** (460 sellers, 78.2%): 
    - Mean violation rate: **3.6%**
    - Contribute **32.9%** of violations (baseline risk)

- **Temporal stability analysis**
  - Monthly cohort analysis across **20 consecutive month-pairs** (2016-10 to 2018-08).
  - **Stability is modest** observed: Mean Jaccard similarity = **~0.25** for Top-50 high-risk sellers.
  - Only **25%** of high-risk sellers remain in the list month-over-month.
  - **Peak stability**: 0.45 (Jun-Jul 2017), indicating brief periods of consistent violators.
  - **Implication**: High-risk seller identity is **transient**, not persistent behavior.

- **Operational insights**
  - **Pareto principle validated**: 10% of sellers drive 37-39% of SLA problems → concentrated intervention is viable.
  - **Dynamic monitoring required**: Low temporal stability means static "blacklists" will miss emerging risks.
  - **Tiered intervention strategy**:
    - High-risk tier: Immediate reactive intervention (proactive capacity audit, priority support).
    - Medium-risk tier: Monitoring with early warning triggers.
    - Low-risk tier: Standard operational procedures.

- **Artifacts saved for downstream analysis**
  - `seller_sla_metrics_180d.parquet`: Seller-level SLA metrics (2,021 sellers).
  - `seller_sla_risk_ranking_180d.parquet`: Risk scores, tiers, and Pareto metrics (588 sellers with ≥10 orders).
  - `seller_sla_risk_stability.parquet`: Monthly Top-50 Jaccard similarity (20 month-pairs).

**Next steps**:
1. **Customer impact & CX validation**: Link seller risk tiers to review scores, NPS proxies, and repeat purchase behavior.
2. **Economic impact & guardrails (GMV at risk)**: Integrate order-level GMV to identify “high-risk + high-GMV” sellers and quantify GMV at risk under different intervention scenarios.
3. **Intervention ROI simulation**: Simulate the cost-benefit of reactive vs. preventive interventions under GMV and CX guardrails.