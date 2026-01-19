# PLAN.md
***Jingtao Yang***

## Optimizing Marketplace Reliability: Identifying High-Risk Sellers to Protect Service Level Agreement and Customer Experience


## 0. Purpose of This Plan

This document defines the execution plan, validation strategy, and core decision logic for this project.

The goal is to ensure the following:
- Every analysis step is linked to a concrete business question
- Every claim is supported by data evidence, statistical tests, or model results
- The final output is able to support real business operational decisions


## 1. Project Scope

### In Scope
- Seller-level operational risk identification
- Quantification of SLA impact on customer experience
- Predictability and early warning analysis
- ROI-driven intervention simulation
- Decision framework design for operations teams

### Out of Scope
- Real-time system deployment
- Black-box models (for interpretability)
- Academic proofs/causal proofs requiring randomized experiments

## 2. Core Hypotheses to Validate

The project is driven by the following core hypotheses:

**H1:** SLA violations are highly concentrated among a small subset of sellers. 

**H2:** SLA violations causally lead to decreased customer experience and retention, and the magnitude of harm increases with delay severity.

**H3:** Severe SLA failures are preceded by detectable early warning signals with sufficient lead time to allow operational intervention.

**H4:** Targeted seller intervention can improve reliability with positive ROI (return on investment).

All the analysis in the project will be designed to validate or invalidate these hypotheses.

## 3. Key Business Questions & Analysis Modules

| Business Question | Analysis Module |
| --- | --- |
| Is risk concentrated? | Seller risk profiling & Pareto analysis |
| Does SLA cause harm? | Matched comparison + temporal analysis |
| Is risk predictable? | Rolling features + walk-forward validation |
| What should we do? | Counterfactual & ROI simulation |
| Where to intervene? | Risk segmentation & decision framework |

## 4. Data Validation Strategy
### Data Sources
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

### Units of Analysis
- Seller-level (primary decision unit)
- Order-level (causality validation)

### Data Integrity Checks
- Count rows & key uniqueness
- Time coverage vaildation
- Missing value patterns analysis
- seller-order linkage verification
  
## 5. Metric Design

Metrics are designed to be:
- Interpretable by non-technical based audiences
- Actionable for business decisions at seller level
- Robust to some parameter changes

### Key Metrics Components
- SLA reliability - delay, severity, violation rate
- Customer experience - reviews, repeat purchase rate, cancellation rate
- Risk contribution - expected SLA impact per seller
- Economic impact - GMV at risk, cost of intervention

Thresholds will be tested through sensitivity analysis.

### Guardrail Metrics (to prevent over-optimization)

To avoid improving SLA at the expense of marketplace health, I define guardrail metrics that must not deteriorate materially:

- Total GMV and order volume
- GMV share from small/long-tail sellers
- New seller activation or onboarding volume (if applicable)

Intervention strategies will be evaluated not only on SLA and CX improvements, but also on their impact on these guardrail metrics.

## 6. Seller Risk Identification Plan

### Objective
Identify sellers whose operational behaviour creates SLA risks

### Steps
1. Aggregate seller-level operational metrics
2. Rank sellers based on the magnitude and frequency of SLA violations
3. Conduct concentration analysis, such as Pareto analysis or Lorenz curve
4. Define preliminary risk tiers

### Validation
- Stability of ranking accross time wondows
- Sensitivity to SLA threshold definitions

## 7. Customer Impact Vaildation Plan

### Objective
Demonstrate that SLA violations cause customer harm, and that the severity of harm increases proportionally with delay length.

### Evidence Strategy

**Level 1: Descriptive Signosts**
- Compare the customer experience metrics between on-time and delayed orders.

**Level 2 - Match Comparison**
- Match sellers/orders on category, price range, geography, and order volume.
- Compare outcomes between high/low risk sellers under matched conditions.

**Level 3 - Within-Seller Analysis**
- Track sellers before and after their 1st major SLA violation.
- Masure changes in review scores, repeat purchase rates, and cancellation rates.

**Level 4 - Dose-Response Analysis**
- Bucket delays by severity, in days range
- Validate monotonic or near-linear degradation in:
  - Review score
  - Cancellation rate
  - 30-day repeat purchase probability

**Level 5 — Threshold Discovery**

Beyond the general dose–response pattern, I will search for potential "cliff points" in delay severity, where customer harm accelerates disproportionately (e.g., repeat purchase drops sharply after 3 more days delay).

This helps inform policy-making such as:
- SLA promises
- Compensation rules for severe delays
- Internal alert thresholds for operations escalation

## 8. Predictability & Lead-time Validation Plan

### Objective
Assess whether high-risk sellers can be flagged with sufficient lead-time to enable operational intervention

### Early Warning Signals
- Rolling delay rates
- Short term validation spikes
- Seller tenure and trends
- Geographic logistics constraints

### Lead-time Evaluation
- Define a severe SLA event, such as delay exceeding threshold
- Evaluate model performance at different lead times:
  - 7-day warning window
  - 14-day ...
  - 21-day ...

### Success Criteria
- Capture rate of severe failures at each lead time
- False positive rate acceptable for ops teams
- Minimum actionable lead time >= 1–2 weeks


## 9. Risk Segementation & Root Cause Analysis

### Purpose
Distinguish between:
- Seller behavioral issues
- Structural logistics issues

### Dimensions
- Gerography
- Category
- Seller maturity
- Carrier dependence

## 10. Financial Impact & ROI Framework (Concise)

### Objective
Translate SLA reliability improvements into economic impact and evaluate whether interventions on high-risk sellers create positive ROI.

### What will be estimated
- Cost of SLA violations:
  - Cancelled orders & wasted acquisition cost
  - Conversion loss from review score drops
  - Lost repeat purchases as an LTV proxy
- Cost of interventions:
  - GMV at risk when restricting high-risk sellers
  - Any additional operational effort

### Scenarios
- Baseline: No intervention, current SLA / CX / GMV.
- Scenario A: Restrict / remove bottom X% high-risk sellers.
- Scenario B: Tiered actions by risk tier (suspend / warn / monitor)

For each scenario I will estimate:
- SLA violations prevented
- Customer experience uplift
- GMV at risk
- Net benefit = avoided SLA cost – intervention cost

### Robustness Check
Key assumptions, such as cost per cancellation, conversion loss per cancellation, will be varied under conservative / base / aggressive settings.

An intervention is considered viable only if ROI stays positive under conservative assumptions.

## 11. Counterfactual & Trade-off Simulation
### Baseline
Observed outcomes with no intervention

### Simulated Interventions
- Remove or throttle high-risk sellers
- Recompute SLA and experience metrics

### Output
Define the trade-off frontier between:
- Growth (GMV)
- Reliability
- Customer experience

## 12. Decision Framework Design

### Risk Tiering
Define seller tiers with:
- Entry criteria
- Recommended actions
- Expected cost vs benefit

### Deliverable
A policy-ready framework usable by operations teams.


## 13. Deliverables

- README.md
- PLAN.md (this doc)
- Modular notebooks (analysis execution)
- Reusable Python modules
- Executive summary

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Correlation mistaken for causation | Multi-layer validation |
| Over-precise ROI claims | Conservative assumptions |
| Overfitting risk signals | Temporal validation |
| Excessive complexity | Interpretability-first design |

## 15. Definition of Success

This project is successful if:
- SLA risk concentration is empirically demonstrated
- Customer harm shows a consistent dose–response relationship
- High-risk sellers can be flagged with >= 14 days lead time
- ROI conclusions remain positive under conservative assumptions
- Results can support a defensible operational decision