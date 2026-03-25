# Seller Early-Warning Signal Analysis – Summary

- **Analysis scope & data**
  - Unit of analysis: individual seller-days (one observation per seller per active date).
  - Time coverage: 2017-01-15 to 2018-08-29 (590 distinct dates), coinciding with the post-warm-up period of the Olist dataset.
  - Panel size: **42,644 seller-days** across **790 sellers** after two filtering steps: (1) seller tenure ≥ 30 days at prediction time (ensures 30-day rolling features are well-defined); (2) lifetime `cum_delivered_orders` ≥ 20 (excludes very thin-history sellers from training and evaluation).
  - Prediction horizons evaluated: **H = 7, 14, 21 days** (does this seller experience ≥1 severe SLA violation in the next H days?).
  - Positive rates by horizon: 11.75% (H=7d), 18.62% (H=14d), 23.94% (H=21d); class imbalance requires threshold-invariant evaluation metrics.
  - Feature set: **37 predictors** across five groups: lifetime structural metrics, last-day snapshot, rolling 7/14/30-day aggregates (volume, delay, violation rate, GMV share), and 7-vs-30-day trend signals.

- **Modelling design**
  - Two candidate models trained on a 70% chronological training window and evaluated on the remaining 30%:
    - **Logistic Regression** (`class_weight='balanced'`, L2 regularisation, `C=1.0`).
    - **LightGBM** (`n_estimators=200`, `num_leaves=31`, `class_weight='balanced'`).
  - Two baselines: a **rule-based score** (primary signal: `severe_violation_gmv_share_30d`; fallback for NaN rows: `lifetime_severe_violation_gmv_share`; zero-fill for sellers with no violation history) and a **random uniform** baseline.
  - Both tails of the train and test windows are trimmed by 21 days to eliminate label leakage across the boundary.
  - **Walk-forward cross-validation**: 5 folds with a 21-day gap between train end and validation start; fold width grows with each iteration (expanding window). Primary CV metrics: ROC AUC and Average Precision (PR-AUC).
  - Primary business evaluation metric: **GMV Recall@K**, defined as the share of future severe-event GMV captured by flagging the top K% of seller-days.

- **Section 6.1–6.2: Walk-forward CV stability**
  - CV AUC by model and horizon (5-fold mean):

    | Horizon | LR AUC (CV) | LightGBM AUC (CV) | LR lead |
    |---|---|---|---|
    | H = 7d | **0.732** | 0.623 | +10.9 pp |
    | H = 14d | **0.726** | 0.646 | +8.0 pp |
    | H = 21d | **0.724** | 0.680 | +4.4 pp |

  - LR **outperforms LightGBM in 4/5 CV folds** across all horizons; the gap is largest at short horizons.
  - LR fold-to-fold AUC variation is modest (range typically < 0.04), indicating stable generalisation across time periods.
  - LightGBM shows **higher inter-fold variance**: at least one fold produces AUC near chance, consistent with sensitivity to training distribution shifts. This substantial fold-to-fold instability distinguishes LightGBM as a noisier model under non-stationarity.
  - **Positive rate drift** is visible across folds: later validation windows have materially higher severe-event rates, confirming temporal non-stationarity in the panel. This is a production consideration, not a modelling error.

- **Section 6.3: Precision-recall analysis (H = 14d)**
  - Evaluated against the no-skill baseline (= class prevalence ≈ 18.6% at H=14d).
  - LR Average Precision: **0.382** vs Rule-based **0.214** vs Random **0.140**; LR delivers 1.78× the AP of the rule-based system.
  - Three operating points identified on the LR PR curve at K = 1% / 5% / 10%:

    | K (% flagged) | LR Precision | LR Event Recall | LR GMV Recall |
    |---|---|---|---|
    | 1% | 0.695 | 4.9% | 9.4% |
    | **5%** | **0.586** | **20.7%** | **27.9%** |
    | 10% | 0.440 | 31.1% | 37.8% |

  - At K = 5%, nearly 3 in 5 flagged seller-days carry a genuine future severe event (Precision = 0.586). This makes the model operationally interpretable; operators can trust a majority of flags.
  - The PR curve confirms that the model remains well above the no-skill line across the full recall range; there is no precision cliff at moderate recall levels.

- **Section 6.4: Test-set discriminative ability (held-out test window)**
  - ROC AUC and Average Precision on the held-out test set (last 30% of dates):

    | Horizon | LR AUC | LightGBM AUC | Rule-based AUC | Random AUC |
    |---|---|---|---|---|
    | H = 7d | **0.763** | 0.716 | 0.684 | 0.493 |
    | H = 14d | **0.753** | 0.713 | 0.673 | 0.496 |
    | H = 21d | **0.746** | 0.709 | 0.664 | 0.499 |

    | Horizon | LR AP | LightGBM AP | Rule-based AP | Random AP |
    |---|---|---|---|---|
    | H = 7d | **0.295** | 0.227 | 0.147 | 0.089 |
    | H = 14d | **0.382** | 0.289 | 0.214 | 0.140 |
    | H = 21d | **0.423** | 0.340 | 0.255 | 0.178 |

  - LR AUC degrades only **1.7 pp** from H=7d (0.763) to H=21d (0.746), confirming meaningful signal persists at a full 3-week lead time. There is no performance cliff beyond H=7.
  - LR consistently outperforms all baselines across every horizon and every metric; the ranking is unambiguous.
  - Note: AP increases with horizon because longer windows have higher positive rates (more positives to recall), not because the model improves; AUC remains the more horizon-comparable metric.

- **Section 6.5: Top-K business metrics (GMV coverage)**
  - Operational question: *how much future at-risk GMV can we protect by flagging the top K% of seller-days?*
  - Results at **K = 5%, H = 14d** (the default operating point):

    | Model | Precision@5% | Event Recall@5% | GMV Recall@5% |
    |---|---|---|---|
    | **LR** | **0.586** | **0.207** | **0.279** |
    | LightGBM | 0.387 | 0.137 | 0.164 |
    | Rule-based | 0.265 | 0.093 | 0.135 |
    | Random | 0.160 | 0.057 | 0.055 |

  - LR captures **27.9% of future severe-event GMV** by flagging only 5% of seller-days, representing **+107% over the rule-based baseline** (13.5%) and **+408% over random** (5.5%).
  - LR captures **20.7% of severe events** in the same 5% budget, representing **+123% over rule-based** (9.3%).
  - Horizon sensitivity at K=5% (LR only):

    | Horizon | Precision | Event Recall | GMV Recall |
    |---|---|---|---|
    | H = 7d | 0.421 | 23.6% | 30.3% |
    | **H = 14d** | **0.586** | **20.7%** | **27.9%** |
    | H = 21d | 0.635 | 17.8% | 24.2% |

  - As horizon increases, precision rises (longer windows accumulate more positives) but recall falls (harder to predict). H=14d offers the best **recall-lead-time balance** for intervention workflows.

- **Section 6.6: Model comparison and selection rationale**
  - LightGBM delivers lower AUC, lower AP, and substantially lower GMV Recall@K than LR across every horizon and K threshold.
  - The performance gap is widest in CV (LR +8–11 pp AUC) but narrows on the test set (LR +3–4 pp AUC). LightGBM exhibits substantial fold-to-fold instability (at least one near-chance fold), suggesting the model overfits to the specific training distribution of early folds and does not extrapolate well to later time periods.
  - Mechanistically: the early-warning signal for short-horizon SLA risk is **approximately linear and temporal**, with recent rolling averages of delay and delivery volume as the dominant predictors. LightGBM's interaction terms and splits add limited explanatory power over a regularised linear model when the underlying signal structure is this simple.
  - LR is also preferable from a governance standpoint: coefficients are interpretable and auditable; LightGBM's non-linear interactions are opaque.

- **Section 6.7: Feature importance and driver interpretation**
  - **Logistic Regression** (H=14d, raw unstandardised coefficients):

    | Rank | Feature | Coefficient | Direction |
    |---|---|---|---|
    | 1 | `delivered_14d` | +0.033 | risk ▲ |
    | 2 | `delivered_7d` | +0.029 | risk ▲ |
    | 3 | `avg_delay_30d` | +0.023 | risk ▲ |
    | 4 | `avg_delay_7d` | +0.021 | risk ▲ |
    | 5 | `avg_delay_14d` | +0.019 | risk ▲ |

  - All top 5 LR drivers are **short-window behavioural signals** (rolling delivery volume and average delay). Violation rate features (`lifetime_violation_rate`, `severe_violation_rate_*d`) carry near-zero coefficients; **historical violation counts add limited incremental value relative to recent delay signals**.
  - *Methodological note*: coefficients are on raw feature scales and are not standardised. Magnitude comparisons across features should be interpreted directionally rather than as exact importance rankings.
  - Delivery volume (`delivered_7/14d`) having positive coefficients reflects a scale effect: higher-volume sellers have more exposure to SLA events in absolute terms.
  - **LightGBM** (H=14d, split gain): concentrates importance on lifetime structural features (`seller_tenure_days`, `cum_delivered_orders`, `cum_delivered_gmv`). This explains LightGBM's underperformance: **seller profile predicts structural risk but not short-horizon behavioural deterioration**, which is what matters for early intervention.
  - Agreement between LR and LightGBM: both identify rolling delay metrics in their top features, but LightGBM over-weights stable structural variables that generalise poorly across time. LR's relative focus on *recent behaviour* is the more valid signal for imminent risk prediction.
  - Implication: a rule-based early-warning system built solely on violation history misses the primary driver of near-term risk, explaining the rule-based system's materially lower recall.

- **H3 Verdict**

  | Evaluation level | Method | Key metric | Support |
  |---|---|---|---|
  | Discriminative ability | ROC AUC on held-out test set (H=14d) | LR 0.753 vs Random 0.496 vs Rule-based 0.673 | **Strong** |
  | Precision-recall | Average Precision / PR-AUC (H=14d) | LR 0.382 vs Rule-based 0.214 (+78%) | **Strong** |
  | GMV coverage | GMV Recall@5%, H=14d | LR 27.9% vs Rule-based 13.5% (+107%) | **Strong** |
  | Event coverage | Event Recall@5%, H=14d | LR 20.7% vs Rule-based 9.3% (+123%) | **Strong** |
  | Lead time | AUC decay from H=7d to H=21d | 1.7 pp drop; signal stable at 3-week horizon | **Strong** |
  | Temporal stability | Walk-forward CV (5-fold, gap=21d) | LR stable; LightGBM shows fold collapse | **Moderate** |
  | Model selection | LR vs LightGBM across all metrics | LR wins: lower CV variance, higher test AUC/AP/Recall@K | **Clear** |

  **H3 is strongly supported.** A logistic regression early-warning model trained on 37 rolling features provides robust 7–21 day lead-time signal, capturing 27.9% of future severe-event GMV at risk by flagging only the top 5% of seller-days, more than double the rule-based baseline coverage.

- **Operational recommendation**

  | Decision | Setting | Rationale |
  |---|---|---|
  | **Deployment model** | Logistic Regression | Higher AUC/AP/Recall@K, lower CV variance, interpretable coefficients |
  | **Default intervention horizon** | 14 days | Best recall-lead-time balance; standard workflow fit |
  | **Extended horizon** | 21 days | Maximum lead time when supply response requires longer planning |
  | **Flagging policy** | Top 5% of seller-days by LR risk score | Precision = 0.586; operationally credible; GMV Recall = 27.9% |
  | **Primary KPI** | GMV Recall@K | Aligns intervention effort with business value at risk |
  | **Secondary KPI** | Precision@K | Governs operational credibility and alert fatigue |
  | **Model governance** | Monitor positive rate drift across periods; retrain on rolling window | Non-stationarity confirmed in CV; static model degrades over time |
  | **Minimum seller history** | ≥30 days of orders | Rolling 30-day features undefined before this threshold |

- **Limitations**
  - All evaluation is **out-of-time** (last 30% of dates), not out-of-seller; generalisation to entirely new sellers with no history is not explicitly validated.
  - **Non-stationarity**: walk-forward CV confirms that positive rates increase over time. A static model trained once will drift; retraining cadence is a production requirement.
  - **Cold-start**: rolling features require ≥30 days of seller history. Newly onboarded sellers cannot be scored until sufficient history accumulates.
  - **Calibration**: model scores are used as a ranking signal (Top-K policy). Absolute probability calibration (required for expected-loss weighting in H4) is not validated here; `class_weight='balanced'` likely introduces systematic miscalibration of raw scores.
  - **No causal identification**: the model produces correlation-based risk rankings, not counterfactual intervention estimates. The link between risk score, intervention, and harm reduction is addressed in H4.
  - **Single severity tier**: the label is binary (any severe violation in the next H days). Severity-weighted labels or multi-class targets (moderate vs severe deterioration) are not explored.

- **Artifacts saved for downstream analysis**
  - `seller_daily_sla.parquet`: Daily seller-level SLA metrics and GMV panel (pre-feature engineering).
  - `seller_early_warning_panel.parquet`: Rolling feature matrix with future labels for all three horizons; input to H4 simulation.
  - `seller_early_warning_metrics_auc.parquet`: Global AUC / AP for all model × horizon combinations (test + CV mean).
  - `seller_early_warning_topk_metrics.parquet`: Top-K business metrics (Precision, Event Recall, GMV Recall) for all model × horizon × K combinations.

**Next steps**:
1. **Intervention ROI simulation (H4)**: Use the H=14d LR risk scores and the severity thresholds established in H2 (3-day cliff) to simulate GMV retained and review-score harm avoided under different intervention scenarios. The early-warning panel parquet provides the feature + label inputs for counterfactual modelling.
2. **Production operationalisation**: Define retraining cadence, monitoring dashboards (positive rate drift, Precision@K decay), and seller communication workflow for flagged accounts.
