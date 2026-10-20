# START HERE - Hotel Booking Cancellation ML

Quick resume sheet. Full project memory is in `CLAUDE.md` (Claude reads it automatically every session).

## 1. Where we are (end of day 1)

| Step | Topic | Status |
|---|---|---|
| 1 | First look at the data | DONE |
| 2 | Data dictionary + leakage audit | DONE |
| 3 | Data quality (clean_v1 created) | DONE |
| **4** | **Target analysis** | **NEXT** |
| 5 | EDA + correlation heatmap | todo |
| 6 | Preprocessing + train/test split | todo |
| 7 | Feature ablation (drop-one / add-one) | todo |
| 8 | All supervised models + hyperparameters | todo |
| 9 | Metrics: formulas + justification (ROC-AUC etc.) | todo |
| 10 | Deployment | todo |
| 11 | Return to Lending Club | todo |

## 2. Read these first tomorrow (in order)

1. `data_exploration/STEP_3_Data_Quality/STEP_3_Data_Quality.pdf` - section 10 has 5 self-check questions. **Answer them to Claude before Step 4.**
2. Re-read `STEP_2_.../STEP_2_Data_Dictionary_And_Leakage.pdf` section 4.2 (the Booking A / Booking B date example) and 4.6 (re-audit).
3. Skim `STEP_1_.../STEP_1_First_Look_At_The_Data.pdf` once.

## 3. The 10 facts you must be able to say in an interview

1. 119,390 rows x 32 columns; one row = one booking. After cleaning: **118,544 rows**.
2. Target `is_canceled`: 37.04% cancelled (Canceled + No-Show). "Always say not cancelled" gives **62.96% accuracy** and catches nothing, so accuracy is a poor metric here.
3. **Leakage = information not available at prediction time (or that encodes the answer).** Our prediction moment is **when the booking is made**. The test for every column: "would I know this at booking time?"
4. **4 leakage columns excluded:** `reservation_status`, `reservation_status_date` (the date is stamped when the outcome happens; a one-line rule on it gets 99.41% accuracy), `assigned_room_type` (rooms are only reassigned for guests who arrive), `required_car_parking_spaces` (all 7,416 bookings with parking have 0.00% cancellations).
5. **Signal vs leakage:** both can be strongly related to the target. Timing decides, not strength. (lead_time = signal; parking = leakage.)
6. A single-column leakage screen is not enough: `reservation_status_date` scored only 0.64 alone but 0.9998 when combined with arrival date (`gap`). Use timing logic + data screens + look for 0%/100% groups.
7. **Suspects** (excluded from the main model under the booking-time rule, ablation will show the score inflation): `booking_changes`, `days_in_waiting_list`; borderline: `total_of_special_requests`.
8. **Duplicates (26.8%) kept** - they are real group bookings (biggest group: 180 identical bookings, all cancelled). Needs a **group-aware split** so identical rows do not land in both train and test.
9. **Zero-night rows all have adr = 0** because adr = revenue / nights is undefined at 0 nights -> dropped. adr = 0 with nights > 0 is kept for classification (Complementary segment = free stays) but excluded from regression.
10. **Irreducible error:** ~1.8% of rows sit in groups of identical features with different outcomes, so no model can be perfect.

## 4. Still unexplained (we will investigate, not guess)

- `deposit_type = Non Refund` cancels **99.36%** of the time (No Deposit 28.38%) - the opposite of common sense.

## 5. How to start tomorrow

Open a terminal in the project folder and start Claude Code, then paste this as your first message:

```
Read CLAUDE.md and START_HERE.md. Start Step 4 (target analysis) after I answer the Step 3 self-check questions. Here are my answers:
1. ...
2. ...
3. ...
4. ...
5. ...
```

Or, if you want to jump straight in: `Read CLAUDE.md and START_HERE.md, then start Step 4.`

## 6. Handy commands (run from the project root)

```bash
# re-run a step's notebook (regenerates outputs, SVGs and CSVs)
python data_exploration/STEP_3_Data_Quality/builders/build_step3_notebook.py

# rebuild a step's PDF from the notebook outputs
python data_exploration/STEP_3_Data_Quality/builders/build_step3_pdf.py

# Step 1 is a plain script
python data_exploration/STEP_1_First_Look/STEP_1_first_look.py

# open a notebook to read/run it cell by cell
jupyter lab data_exploration/STEP_3_Data_Quality/STEP_3_data_quality.ipynb
```

Replace `3` with `2` for the Step 2 equivalents. Do not use `python -I` (it hides pandas).

## 7. Folder map

```
hotel-booking-cancellation-ml/
  CLAUDE.md          project memory (Claude updates it after every step)
  START_HERE.md      this file
  data/              hotel_bookings.csv (raw), hotel_bookings_clean_v1.csv (git-ignored)
  data_exploration/
    _shared/pdf_common.py
    STEP_1_First_Look/        PDF, .py, builders/
    STEP_2_Data_Dictionary/   PDF, .ipynb, CSV, figures/ (SVG), builders/
    STEP_3_Data_Quality/      PDF, .ipynb, 2 CSVs, figures/ (SVG), builders/
```

## 8. Working rules (already in CLAUDE.md)

- Claude writes all code, makes the technical decisions, explains the WHY before the HOW, and corrects you plainly when you are wrong.
- One detailed PDF per step, in its own folder, with libraries listed, interview questions + answers, and a self-check. Charts are SVG only. No mention of the CTO inside PDFs.
- Small steps; Claude asks before installing anything.
- Planned for Step 6: group-aware split; fill missing values only after the split (company -> has_company flag, agent -> "no agent", country -> "Unknown", children -> 0, meal Undefined -> SC).
