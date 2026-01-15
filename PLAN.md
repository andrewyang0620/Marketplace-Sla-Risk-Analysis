# PLAN.md
***Jingtao Yang***

## Optimizing Marketplace Reliability: Identifying High-Risk Sellers to Protect Service Level Agreement and Customer Experience


## 0. Purpose of This Plan
This document defData Integrity Checksines the excutive plan, vaildation strategy, and core logic for decision making in this project.

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

**H2:** SLA violations causally lead to decreased customer experience and retention.

**H3:** Severe SLA failures are preceded by detectable early warning signals.

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
  
## Metric Design
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

