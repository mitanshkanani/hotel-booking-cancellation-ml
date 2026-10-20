# Hotel Booking Cancellation ML - Project Memory

> **RULE: After EVERY completed step, update this file** (Progress Log, Key Findings, Decisions, Open Questions, Folder Structure). Do it before telling Mitansh the step is done. Keep it accurate; this file is how context survives between sessions.

## 1. Who and why
- **User:** Mitansh, B.Tech Computer Engineering student preparing for AI/ML roles. Not applying to jobs now, so there is no rush.
- **Why this project:** An earlier Lending Club project (151 columns, finance domain) was built fast with AI help and was not understood end to end. Mitansh could not explain feature correlations, could not justify the metric (ROC-AUC vs accuracy), and did not know the formulas. Lending Club is paused and removed from the resume. This medium-scale project builds the foundation, then goes on the resume; afterwards the same discipline is applied to finish Lending Club.
- **Real goal:** NOT just a model. Mitansh must understand how the data behaves and defend every decision in an interview: why these features, what happens when a feature is removed or added, why this metric and its formula, why each preprocessing step. Model building is the LAST step, not the first.

## 2. Roles
- **Mitansh:** the learner. Reads every PDF closely, answers the self-checks, and must be able to explain every decision in an interview. Mitansh has said explicitly: "I am not the expert here, you are; you are teaching me."
- **Claude:** the expert and teacher. Writes ALL the code, **makes the technical decisions and states them firmly with reasons** (never "this is your decision" or "awaiting your confirmation"), and **tells Mitansh plainly when an answer is wrong or partly wrong**. Explains the WHY before the HOW. Teach so that Mitansh can defend each decision.
- **GPT:** research only (found the dataset).

## 3. Dataset
- Hotel Booking Demand, Kaggle `jessemostipak/hotel-booking-demand`. Paper: "Hotel Booking Demand Datasets" (Antonio, Almeida, Nunes). City hotel and Resort hotel in Portugal, 2015-2017.
- File: `data/hotel_bookings.csv` (16.9 MB). **Verified: 119,390 rows x 32 columns.** One row = one booking. `data/` is git-ignored.
- **Task 1 (main): classification** - predict `is_canceled` (0/1). Verified balance: 62.96% not cancelled (75,166), 37.04% cancelled (44,224). Majority-class baseline accuracy = 0.6296.
- **Task 2 (secondary): regression** - predict `adr` (Average Daily Rate = total room revenue / nights).
- The tasks are separate models. adr may be an input to the cancellation model (it is quoted at booking time); `is_canceled` must NOT be an input to the adr model (leakage).
- **Verified in Step 2:**
  - `is_canceled = 1` = Canceled (43,017) + **No-Show (1,207)**. Check-Out (75,166) = 0.
  - Real missing: `company` 112,593 (94.31%), `agent` 16,340 (13.69%), `country` 488 (0.41%), `children` 4. agent/company are IDs (333/352 distinct), not quantities.
  - Hidden missing ("Undefined"): `meal` 1,169, `market_segment` 2, `distribution_channel` 5.
  - Oddities queued for Step 3: adr min -6.38 and max 5400, adults max 55 and zero-adult rows, babies/children max 10, weeknights max 50, weekend nights max 19, zero-night stays, lead_time max 737 (median 69, mean 104), days_in_waiting_list max 391.
  - **Leakage CONFIRMED (4 columns, excluded from features):**
    - `reservation_status` - maps exactly onto the target (single-column AUC 1.0000).
    - `reservation_status_date` - stamped when the outcome happens: = departure date on 99.96% of Check-Outs; = cancellation date (median 56 days before arrival) on Canceled rows. One-line rule "status_date - arrival_date <= 0 -> cancelled" gets 99.41% accuracy with no model; `gap` AUC 0.9998 although the raw date alone scores only 0.638.
    - `assigned_room_type` - partial leak, decided by timing/mechanism: room changed -> 5.38% cancel vs 41.56% (rooms are only reassigned for guests who arrive); room_changed AUC only 0.585 because it covers ~12.5% of rows.
    - `required_car_parking_spaces` - found in the re-audit: all 7,416 bookings with 1+ spaces have exactly 0.00% cancellations (recorded only for guests who arrive).
  - **Leakage SUSPECTS to settle by ablation:** `booking_changes` (final count; 0 -> 40.85% cancel, 1 -> 14.23%), `days_in_waiting_list` (>0 -> 63.79% cancel vs 36.19%), `total_of_special_requests` (0 -> 47.72%, 3+ -> 16.82%; gradual, timing suspect).
  - Strong but LEGITIMATE: `previous_cancellations` > 0 -> 91.64% cancel; `is_repeated_guest` 14.49% vs 37.79%; `lead_time`, `country`, `deposit_type` (single-column AUCs 0.69 / 0.70 / 0.66).
  - Counter-intuitive, unexplained: `deposit_type = Non Refund` cancels 99.36% (No Deposit 28.38%). Investigate in EDA (by hotel, year, segment, country); do not invent a reason.
  - **Lesson recorded:** a single-column leakage screen (depth-5 tree, 5-fold CV ROC-AUC) only caught reservation_status; other leaks hide in relationships between columns or in timing. Use timing logic + data screens + look for 0%/100% groups. An audit can never prove zero leakage; ablation and a "too good to be true" rule are further safeguards.
  - Verdict counts over 32 columns: 10 USABLE, 17 NEEDS CARE, 4 LEAKAGE, 1 TARGET (see `data_exploration/STEP_2_Data_Dictionary/STEP_2_column_dictionary.csv`).
- **Verified in Step 3 (data quality):**
  - Duplicates: 31,994 full-row 2nd+ copies (26.80%); 8,171 duplicate groups; rows in duplicate groups cancel 58.39% vs 26.22% for unique rows. Concentrated in Groups (84.4% of its rows) and Offline TA/TO (50.4%); the six biggest groups (99-180 identical bookings) were ALL cancelled: real batch bookings. 289 feature-identical groups (2,107 rows, ~1.8%) contain both outcomes = irreducible label noise.
  - Zero guests: 180 rows. Zero nights: 715 rows, ALL with adr exactly 0 (adr = revenue/nights is undefined at 0 nights), cancel rate 4.9%. 70 rows overlap.
  - adr: 1 negative (-6.38); 1,959 rows adr = 0 (Complementary segment is 91.5% adr 0 = free stays by design); max 5400 (next highest 510, p99.99 = 388).
  - 16 rows with 5-55 adults: all Resort, all cancelled, all adr 0, clustered at the start of the file (placeholder-like). 3 rows with 10 children / 9-10 babies.
  - **clean_v1 = `data/hotel_bookings_clean_v1.csv`: 118,544 rows x 32 columns** (removed 846 rows = 0.71%; cancel rate 37.04% -> 37.25%). 117,395 rows have adr > 0 (regression set); 1,149 rows adr = 0 stay for classification only.
  - Kept on purpose: duplicates, lead_time >= 500 (481 rows, 85.65% cancel), total_nights >= 15 (439), adr 300-1000 (275), 223 rows with zero adults but children/babies.

## 4. Business use case (for explanations)
Cancellation probability per booking, summed per arrival date, gives expected real guests. Uses: overbooking (sell more than rooms, e.g. 120 bookings for 100 rooms at 30% cancel), staffing and inventory planning weeks ahead, deposit policy, retention outreach. Over-estimating cancellations means overbooking and guests with no room; under-estimating means empty rooms. The two errors cost differently, which drives metric choice. ADR regression supports pricing checks and revenue-at-risk = P(cancel) x adr x nights.

## 5. Roadmap
1. First look (shape, dtypes, rows, target balance) - DONE
2. Data dictionary and leakage audit: all 32 columns, missing counts, unique values, verdict - DONE
3. Data quality: duplicates, zero-guest, zero-night, adr outliers, extreme values, with reasons - DONE (produces clean_v1)
4. Target analysis and imbalance implications
5. EDA feature by feature, then correlation heatmap (teach Pearson r, limits, multicollinearity)
6. Preprocessing, every decision justified
7. Feature ablation, both directions: drop-one (all features, remove one, retrain, compare) and add-one (base set, add one, retrain, compare). Same split/seed/model so differences are signal, not noise. Always explain WHY the score changed.
8. All important supervised models, compared across metrics and hyperparameters
9. Metrics with formulas and when right/wrong: accuracy, precision, recall, F1, TPR, FPR, ROC (Receiver Operating Characteristic: TPR vs FPR across thresholds), AUC, PR-AUC; regression MAE, RMSE, R2. Note: precision depends on class ratio; recall and ROC-AUC do not.
10. Deploy the final model
11. Return to Lending Club

## 6. How to work with Mitansh (preferences)
- Small steps. Explain the WHY before the HOW. After running something, explain in detail why it was done.
- Simple language; finance knowledge is weak, but all of supervised learning has been covered. If something is not understood, re-explain with a concrete example (as done for the date leak: two bookings A and B).
- Quiz and challenge like an interviewer; add likely interview questions (with answers) to every PDF.
- Rate Mitansh's self-check answers honestly and correct mistakes directly.
- Flag data leakage, overfitting and misleading metrics whenever they appear.
- Ask before changing the environment (installs etc.).
- Re-check your own earlier verdicts when evidence contradicts them and say so openly (e.g. parking was first marked "needs care" and corrected to leakage).
- Avoid overstating: report what the numbers show (e.g. room_changed is a partial leak, AUC 0.585).

## 7. Documentation rules
- **One folder per step:** `data_exploration/STEP_<n>_<Topic>/` containing: the PDF, the executed notebook (`.ipynb`) or script (`.py`), output files (CSV), `figures/` (SVG) and `builders/` (scripts that generate the notebook and PDF). Shared PDF helpers live in `data_exploration/_shared/pdf_common.py`. Later stages follow the same pattern.
- **One PDF per topic, DETAILED** (Mitansh wants detail, not short PDFs, but one topic each so it stays digestible). Name: `STEP_<n>_<Topic>.pdf`.
- **Every PDF must:** list the libraries used (with versions) and why; list the files of that step; explain what was done AND why; include formulas where relevant; use a concrete worked example for any concept that is hard (two-booking example style); include interview questions with model answers; end with a self-check and a pointer to the next step.
- **Do not mention the CTO or the original feedback inside PDFs.** (Fine to discuss in chat.) Do not write "your decision" or "awaiting confirmation" in PDFs; state the decision and the reason.
- **Save every .py / .ipynb that was run** in its step folder. Storing everything is fine.
- **From Step 2 on, work in a Jupyter notebook** `STEP_<n>_<topic>.ipynb` (small, focused steps: not too big, not too small), executed so outputs are saved; markdown cells explain the WHY. The notebook is generated by `builders/build_step<n>_notebook.py` (+ `step<n>_extra_cells.py`) with nbformat + nbclient; fix bugs in the builder source and re-run so the notebook always matches its builder.
- **Images: SVG ONLY** for the whole project, saved in the step's `figures/` folder (matplotlib `savefig(...svg)`). Never save PNG or both. Embed in PDFs with svglib via `_shared/pdf_common.py` (`Doc.figure`). Temporary PNG renders for visual checking go in the scratchpad only.
- `pdf_common.py` provides styles, tables (with verdict colours), figures, Q&A blocks; use it for Step 3 onwards (Step 1 builder is standalone).
- The correlation heatmap belongs to Step 5 (needs cleaned data); save it as SVG too.
- PDFs are built with reportlab. Avoid Unicode sub/superscripts and symbols like arrows or the approx sign in Helvetica (they render as boxes); use ASCII or `<sub>`/`<super>` tags. Render a page to PNG and look at it after building.

## 8. Environment
- Windows 11, shell PowerShell/Git Bash, Python 3.14.6. Installed: pandas 2.3.3, numpy 2.5.2, scikit-learn 1.9.0, matplotlib 3.11.1, scipy 1.18.0, seaborn 0.13.2 (installed in Step 1), svglib 2.3.0 (installed in Step 2 with Mitansh's approval), reportlab 5.0.1, pypdf, pypdfium2, jupyter, nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.4.0. nbconvert is NOT installed.
- Do not run Python with `-I` here: pandas etc. live in user site-packages, which isolated mode ignores ("No module named pandas").
- Git: branch `main`, no commits yet; `.gitignore` contains `data/`. Do not commit or push unless asked.

## 9. Folder structure
```
hotel-booking-cancellation-ml/
  CLAUDE.md                          (this file - update after every step)
  .gitignore                         (data/)
  data/hotel_bookings.csv            (git-ignored)
  data_exploration/
    _shared/pdf_common.py
    STEP_1_First_Look/
      STEP_1_First_Look_At_The_Data.pdf
      STEP_1_first_look.py
      builders/build_step1_pdf.py
    STEP_2_Data_Dictionary/
      STEP_2_Data_Dictionary_And_Leakage.pdf
      STEP_2_data_dictionary.ipynb
      STEP_2_column_dictionary.csv
      figures/ step2_missing_values.svg, step2_suspect_cancel_rates.svg, step2_single_feature_auc.svg
      builders/ build_step2_notebook.py, step2_extra_cells.py, build_step2_pdf.py
    STEP_3_Data_Quality/
      STEP_3_Data_Quality.pdf
      STEP_3_data_quality.ipynb
      STEP_3_row_removal_log.csv, STEP_3_quality_decisions.csv
      figures/ step3_adr_distribution.svg, step3_rows_removed_per_rule.svg
      builders/ build_step3_notebook.py, step3_extra_cells.py, build_step3_pdf.py
  data/hotel_bookings_clean_v1.csv   (created in Step 3; git-ignored)
```

## 10. Progress log
- **Step 1 - First look: DONE.** Installed seaborn. Verified shape (119,390 x 32), dtypes (12 text columns; children/agent/company are float because of NaN; dates stored as text), target balance, and baseline accuracy 0.6296. Observed in the first 3 rows: lead_time 737, adr = 0 with real check-outs, 0-night stays, reserved vs assigned room differing, agent/company NaN, reservation_status = Check-Out matching is_canceled = 0. Output: STEP_1 PDF (7 pages) + `.py`. Later corrected the PDF sentence about reservation_status to "Canceled or No-Show".
- **Step 2 - Data dictionary and leakage audit: DONE (revised once).** Notebook-based (see Section 3 for verified facts). Output: STEP_2 PDF (11 pages), `.ipynb` (30 cells), dictionary CSV, 3 SVG charts. Installed svglib. Mitansh's Step 1 self-check answers were good (about 8/10); corrections given in chat: precision depends on class ratio (recall and ROC-AUC do not); assigned_room_type is leakage because of the mechanism, not because "the model sees a change"; the adr = 0 rows were Check-Outs, so the question is free stay vs data error. Mitansh did not understand section 4.2 (reservation_status_date): rewritten with two worked bookings and a one-line rule test (99.41%). Re-audit added (single-column screen, pair features, parking leak found). Folder reorganised into per-step folders.

- **Step 3 - Data quality: DONE.** Notebook-based. Output: STEP_3 PDF (9 pages), `.ipynb`, 2 CSVs, 2 SVG charts, `data/hotel_bookings_clean_v1.csv`. Mitansh passed the Step 2 check-in (signal vs leakage, booking_changes timing); the No-Show vs Canceled question was explained in chat (notice period: median 56 days for cancellations vs none for no-shows; 1,207 rows = 2.7% of positives). Removal rules are value-based, never label-based. Statistical fixes (imputation, encoding, scaling) deferred to Step 6, after the split.

## 11. Open questions / to verify next (Step 4 onward)
- Why deposit_type Non Refund cancels 99.36% (EDA).
- Step 6 must implement: group-aware train/test split (identical-feature bookings stay together; also consider time-based split); imputation/encoding fitted on train only; sensitivity test with duplicates dropped.
- Step 10 (deployment): input validation, e.g. reject/flag 0-night or 0-guest bookings (model never saw them).
- Regression: use adr > 0 rows only; consider log(adr) / MAE because RMSE is outlier-sensitive.
- Whether meal 'Undefined' should be merged with 'SC' (documentation says both = no meal package).
- Decide arrival_date_year handling and time-based split vs random split.
- booking_changes, days_in_waiting_list, total_of_special_requests: keep or drop - settle with ablation.

## 12. Decisions made (by Claude, with reasons; Mitansh learns to defend them)
- **Exclude as features (leakage):** `reservation_status`, `reservation_status_date`, `assigned_room_type`, `required_car_parking_spaces`. Reason: each is created at or after the outcome (evidence in the Step 2 PDF).
- **Prediction moment = the moment the booking is made.** Every feature must be available then. This is the master rule for leakage decisions. Ablation measures how much each suspect inflates the score; it does NOT decide legitimacy (timing does).
- **Suspects `booking_changes`, `days_in_waiting_list`, `total_of_special_requests`:** under the booking-time rule, `booking_changes` (always 0 at booking; dataset only has the final count) and `days_in_waiting_list` (known only after confirmation) are EXCLUDED from the main model. `total_of_special_requests` is borderline (final count includes later additions): run ablation, exclude conservatively if it contributes a large share. Still run ablation on all three in Step 7 to show the score inflation (interview material).
- **Keep `previous_cancellations`, `is_repeated_guest`, `lead_time`, `country`, `deposit_type` as legitimate** (known at booking); `deposit_type` still needs its oddity explained.
- **Target definition:** `is_canceled` as given (Canceled + No-Show = 1); say so explicitly whenever the project is explained.
- **All charts are SVG only.**
- **Step 3 decisions:** DROP zero-guest (180), zero-night (715), negative adr (1), adr 5400 (1), 5+ adults (16), 4+ children / 3+ babies (3) = 846 unique rows -> clean_v1. KEEP duplicates (real group bookings) with a group-aware split. KEEP adr = 0 for classification, EXCLUDE from regression. PLAN for Step 6: company -> has_company flag; agent -> "no agent" category; country -> "Unknown"; children NaN -> 0; meal Undefined -> merge with SC; market_segment/distribution_channel Undefined -> own category.
