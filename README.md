# Optimizing Marketplace Reliability: Identifying High-Risk Sellers to Protect Service Level Agreement and Customer Experience

![Business Analytics](https://img.shields.io/badge/Business-Analytics-blue)
![Python](https://img.shields.io/badge/Python-3.13.5-green)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter)
<!-- ![License](https://img.shields.io/badge/License-MIT-yellow) -->
![Status](https://img.shields.io/badge/Status-In--Progress-orange)


## Executive Summary
<!-- - **Concentrated Risk:** Analysis reveals that the top `5%` of high-risk sellers are responsible for `over 45%` of total platform SLA violations.
- **Impact:** `SLA breaches` are the #1 driver of negative sentiment; orders with `>3` days delay show a `60%` drop in `30-day` repeat purchase probability and a `2.4x` increase in cancellation rates.

- **Predictive Signals:** `80% of` severe failures are preceded by `"micro-delay"` patterns in seller processing time within a `14-day` lookback window.

- **Strategic Trade-off:** Implementing a tiered intervention strategy can reduce platform-wide delays by `20%` while risking less than `2%` of total GMV, optimizing the long-term LTV/GMV balance. -->


## 1. Project Motivation
### Why Identifying High-Risk Sellers Matters

As marketplaces scale, operational failures are rarely evenly distributed. A small subset of sellers can disproportionately undermine platform reliability by repeatedly missing delivery SLAs, triggering cancellations, and eroding customer trust.

Left unmanaged, these failures compound:
- They degrade customer experience and reduce repeat purchase likelihood
- They increase operational costs through refunds and support burden
- They threaten long-term platform credibility

The challenge is not whether poor-performing sellers exist, but whether their risk can be **identified early and managed economically** without sacrificing growth.


## 2. Key Business Questions
 1. Is SLA risk evenly distributed across sellers, or highly concentrated?
   
    *Why it matters:* If risk is concentrated, we can achieve high impact with low operational cost.

 2. Do SLA violations causally harm customer experience and retention?

    *Why it matters:* We need to prove that a delay is not just a bad review, but a direct cause of customer churn and reduced purchase frequency.

 3. Can high-violating-sellers be identified prior to severe SLA breaches? What are the early warning signals of a failing seller?
   
    *Why it matters:* Early identification allows for proactive intervention, reducing the incidence of severe SLA violations.

 4. What intervention stratigies can be applied to maximize the reliability imporovement per unit of GMV at risk? What is the optimal threshold for seller intervention?
   
    *Why it matters:* Balance the trade-off between improving reliability and risking GMV by intervening with sellers.

 5. Attribution: Seller Performance vs. Logistics Infrastructure

    *Why it matters:* Understanding the root causes of SLA violations helps in designing targeted interventions, whether they involve seller training or logistics improvements.

## 3. Data Source and Scope
### Data Source
- **Brazilian E-Commerce Public Dataset** by Olist


