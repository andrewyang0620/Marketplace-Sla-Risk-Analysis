# Customer Impact Analysis – Summary

- **Analysis scope & data**
  - Unit of analysis: individual delivered orders linked to reviews and customers.
  - Time coverage: full Olist period (2016-09-04 to 2018-10-17), consistent with `orders_sellers` SSoT.
  - Panel size: **99,441 orders** after joining with reviews and customer table; `review_score` missing rate is **0.77%** (imputed/excluded per analysis level).
  - Core CX metrics tracked: `review_score`, `is_low_rating` (≤3), `is_canceled`, `repeat_within_horizon` (30-day repeat purchase).
  - Delay buckets: on-time/early (90,442), 1–2 days late (1,374), 3–5 days late (1,403), 6+ days late (3,786); 2,987 orders have no delay bucket (non-delivered or missing timestamps).

- **Level 1 – Descriptive signposts (on-time vs violation)**
  - On-time orders: **n = 92,906**; SLA violation orders: **n = 6,535**.
  - Mean review score: **4.21** (on-time) → **2.27** (violation), diff = **−1.94 pts**.
  - Low-rating rate (≤3): **19.3%** (on-time) → **71.6%** (violation), diff = **+52.3 pp** (~3.7× increase).
  - Very low-rating rate (≤2): **11.3%** → **60.9%**, diff = **+49.6 pp**.
  - Bootstrap 95% CI (2,000 resamples):
    - diff mean_review: **[−1.982, −1.900]**
    - diff low_rating_rate: **[+0.511, +0.534]**
  - **Formal statistical tests:**
    - Mann-Whitney U test (review_score, one-sided): **U = 479,684,619, p < 0.001** — on-time orders are stochastically higher in review score. Non-parametric; robust to the J-shaped review distribution.
    - Chi-square test (low_rating_rate, 2×2 contingency): **χ² = 9,524.0, df = 1, p < 0.001** — proportion of low ratings is significantly different between groups.
  - Cancellation rate is **lower** for violations (0.02% vs 0.67%) — selection artifact: shipped orders are rarely canceled.
  - 30-day repeat rate: 0.43% (violation) vs 0.56% (on-time), diff = −0.13 pp — directionally correct but too small for reliable inference at this time horizon.

- **Level 4 – Dose–response (delay bucket gradient)**

  | Delay bucket | Orders | Mean review | Low-rating rate |
  |---|---|---|---|
  | on_time_or_early | 89,941 | **4.29** | **17.3%** |
  | 1–2 days late | 1,370 | 3.51 | 40.3% |
  | 3–5 days late | 1,400 | **2.47** | **66.9%** |
  | 6+ days late | 3,765 | **1.74** | **84.7%** |

  - Mean review score falls **monotonically** across all four buckets: 4.29 → 3.51 → 2.47 → 1.74.
  - Low-rating rate rises monotonically: 17.3% → 40.3% → 66.9% → 84.7%.
  - The **steepest single-step deterioration** occurs at the **3-day boundary** (1–2d → 3–5d late): −1.04 review pts, +26.6 pp low-rating rate.
  - At 6+ days late, **85% of orders** receive a low rating — severe delay is perceived as near-universal failure.
  - Cancellation rate remains near zero across all delay tiers (~0.03% at 6+ days); pre-shipment cancellations are excluded from delay buckets, making cancel rate a non-signal in the dose framework.

- **Level 2 – Stratified comparison (approx. matched analysis)**
  - Analysis run one dimension at a time to avoid over-granularity:
    - **29 product categories** (groups ≥30 orders on both sides).
    - **21 customer states** (groups ≥30 orders on both sides).
  - SLA violation effect on **low-rating rate is positive in 100% of strata** (50 total).
  - SLA violation effect on **repeat rate is negative or zero in 100% of strata**.
  - Effect magnitude across strata: diff low-rating typically **+42 pp to +70 pp** — large and consistent.
  - **No exculpatory stratum found.** The aggregate Level 1 result is not driven by category or geographic composition.

- **Level 3 – Within-seller before/after analysis**
  - Sellers with ≥1 severe violation and ≥5 orders on each side of a 90-day pre/post window.
  - **Pre-event**: 10,186 orders (90-day window before first severe violation).
  - **Post-event**: 17,588 orders (90-day window after first severe violation).

  | Metric | Before | After | diff |
  |---|---|---|---|
  | Mean review score | **4.19** | **3.98** | **−0.21** |
  | Low-rating rate | **20.1%** | **25.6%** | **+5.5 pp** |
  | Cancellation rate | 0.37% | 0.19% | −0.18 pp |
  | 30d repeat rate | 0.67% | 0.59% | −0.08 pp |

  - The **same sellers** show degraded review quality after a severe SLA event. Unmeasured seller-level confounders (product quality, price) are differenced out by using the seller as its own control.
  - Effect size is attenuated vs Level 1 (−0.21 vs −1.94 for mean_review) because post-event orders are mostly on-time — the post-period captures **reputational spillover**, not just delayed orders.
  - **Volume bias caveat**: post-period order count (~17,588) is 73% higher than pre-period (~10,186). Sellers in a severe-violation episode are often in a growth phase; this does not invalidate metric comparisons but warrants conservative reading.

- **Level 5 – Threshold discovery**
  - Adjacent-bucket deltas confirm the **3-day boundary as the primary policy cliff point**:
    - on-time → 1–2d late: −0.78 review pts, +23.1 pp low-rating
    - **1–2d → 3–5d late: −1.04 review pts, +26.6 pp low-rating** ← steepest step
    - 3–5d → 6+ late: −0.73 review pts, +17.7 pp low-rating
  - A two-tier SLA severity policy (moderate: 1–2 days; severe: 3+ days) is data-driven — the 3-day mark is not arbitrary.

- **H2 Verdict**

  | Level | Method | Key result | Support |
  |---|---|---|---|
  | L1 Descriptive | Global on-time vs violation | diff review −1.94 (p<0.001); diff low-rating +52.3 pp (p<0.001) | **Strong** |
  | L2 Stratified | Within-category / state | Effect consistent in 100% of 50 strata | **Strong** |
  | L3 Within-seller | Pre/post first severe event | diff review −0.21, diff low-rating +5.5 pp | **Moderate** |
  | L4 Dose–response | Delay bucket gradient | Monotone decline; no counter-examples | **Very strong** |
  | L5 Threshold | Adjacent-bucket deltas | Cliff at 3-day mark across both metrics | **Actionable** |

  **H2 is strongly and consistently supported across all five analytical levels.**

- **Policy implications**
  - **Use 3+ days late as the severe SLA tier boundary** for escalation triggers and customer compensation policy.
  - **Review score and low-rating rate are the primary CX KPIs** for SLA monitoring dashboards; 30-day repeat rate is too noisy at this time window to be actionable.
  - **Severe violations cause reputational spillover** — they taint subsequent on-time orders from the same seller. Interventions should target sellers *before* the first severe event, not reactively after.
  - **Dose–response justifies graduated intervention**: moderate delay (1–2d) may warrant a warning; severe delay (3+ days) warrants immediate proactive support or financial penalty.

- **Limitations**
  - All analyses are observational — no causal identification (no DiD, no IV, no RCT).
  - Level 3 volume bias: post-period order count is ~73% larger than pre-period.
  - Level 2 uses stratification only; residual within-stratum confounding is possible.
  - Cohort anchored at first severe violation only; gradual deterioration across multiple events may be under-estimated.
  - 30-day repeat rate is structurally low (0.55% overall) in this marketplace, limiting its statistical power for H2 validation.

- **Artifacts saved for downstream analysis**
  - `order_customer_panel_30d.parquet`: Order-level panel linking SLA flags, CX metrics, and delay buckets.
  - `cx_level1_sla.parquet`: Level 1 aggregate CX summary by SLA flag.
  - `cx_dose_response.parquet`: Dose–response summary by delay bucket.
  - `cx_stratified_sla_violation.parquet`: Stratified deltas by category and state.
  - `cx_within_seller_per_seller.parquet` / `cx_within_seller_overall.parquet`: Level 3 before/after results.

**Next steps**:
1. **Early warning model (H3)**: Predict which sellers will transition into the high-risk tier in the next 30 days using rolling SLA features — motivated by both H1 (risk concentration) and the reputational spillover finding here.
2. **Intervention ROI simulation (H4)**: Use the 3-day threshold and Level 1 CX deltas to simulate the customer harm avoided (in review score units and GMV retained) under different intervention scenarios.
