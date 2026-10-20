"""Builds STEP_2_Data_Dictionary_And_Leakage.pdf from the executed notebook outputs.

Run from anywhere:  python data_exploration/STEP_2_Data_Dictionary/builders/build_step2_pdf.py
"""
import sys
from pathlib import Path

import pandas as pd
from reportlab.lib.units import mm

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '_shared'))
from pdf_common import Doc, SMALL  # noqa: E402

FOLDER = Path(__file__).resolve().parent.parent
FIG = FOLDER / 'figures'
dic = pd.read_csv(FOLDER / 'STEP_2_column_dictionary.csv')

d = Doc()
d.H1('STEP 2 - Data Dictionary and Leakage Audit')
d.P('Hotel Booking Cancellation Project | Data Exploration series', SMALL)
d.SP(4)
d.NT('<b>What this PDF is:</b> a fact sheet for every one of the 32 columns (type, missing values, distinct values) '
     'and a verdict on each: is it safe to use as a feature? All numbers come from the notebook '
     '<b>STEP_2_data_dictionary.ipynb</b> in this same folder, which you can re-run cell by cell.')

d.H2('Files for this step')
d.table([
    ['File', 'What it is'],
    ['STEP_2_data_dictionary.ipynb', 'The notebook that produced every number and chart here (run top to bottom).'],
    ['STEP_2_column_dictionary.csv', 'The full 32-row dictionary table (open in Excel if you like).'],
    ['figures/step2_missing_values.svg', 'Chart 1: missing values per column.'],
    ['figures/step2_suspect_cancel_rates.svg', 'Chart 2: cancellation rate for the leakage suspects.'],
    ['figures/step2_single_feature_auc.svg', 'Chart 3: single-column predictive power (leakage screen).'],
], [70 * mm, 104 * mm])

d.H2('Libraries used in this step')
d.table([
    ['Library', 'Version', 'Why we use it here'],
    ['pandas', '2.3.3', 'Column profile, value counts, crosstab, groupby cancellation rates, date arithmetic.'],
    ['numpy', '2.5.2', 'Numeric helpers for the chart positions.'],
    ['matplotlib', '3.11.1', 'Draws the two charts. Saved as SVG only (one image format for the whole folder).'],
    ['scikit-learn', '1.9.0', 'DecisionTreeClassifier + cross_val_score + StratifiedKFold for the leakage screen (cross-validated ROC-AUC).'],
    ['nbformat + nbclient', '5.11.1 / 0.11.0', 'Build and execute the notebook so the saved outputs are real.'],
    ['svglib', '2.3.0', 'Installed in this step so the SVG charts can sit inside the PDF as sharp vector graphics.'],
    ['reportlab', '5.0.1', 'Builds this PDF.'],
], [34 * mm, 30 * mm, 110 * mm])

# ------------------------------------------------------------------ 1
d.H2('1. Why build a data dictionary before cleaning anything?')
d.P('Cleaning without a plan is blind. The dictionary tells us, column by column, <b>what exists, what is broken, and what '
    'must never be used</b>. It also forces the most important question in applied ML: <i>"Would I know this value at the '
    'moment I need the prediction?"</i> A column that fails this test is leakage, and a model built on leakage looks '
    'brilliant in testing and fails in real use.')
d.P('For every column we record four facts:')
d.B(['<b>dtype</b> - what pandas thinks the column is (number or text).',
     '<b>missing</b> - how many values are empty, and what % of the 119,390 rows that is.',
     '<b>n_unique</b> (also called <b>cardinality</b>) - how many different values the column has. 2 values means a flag, '
     '10 means a category, 8,879 means a continuous number.',
     '<b>verdict</b> - USABLE, NEEDS CARE, LEAKAGE, or TARGET, with the reason written down.'])

# ------------------------------------------------------------------ 2
d.H2('2. Missing values')
d.P('Only four columns contain real blanks:')
d.table([
    ['Column', 'Missing rows', '% of 119,390', 'Why it matters'],
    ['company', '112,593', '94.31%', 'Almost empty. A typical choice is to reduce it to a "has a company" yes/no flag, or drop it.'],
    ['agent', '16,340', '13.69%', 'Missing probably means "no travel agent" - which is information, not just a gap.'],
    ['country', '488', '0.41%', 'Small gap. Many ways to handle (new category, most frequent value).'],
    ['children', '4', '0.00%', 'Only 4 rows. This is why the column is float, as Step 1 predicted.'],
], [24 * mm, 26 * mm, 26 * mm, 98 * mm])
d.figure(FIG / 'step2_missing_values.svg', 140, 'Chart 1 - Missing values per column. Source: notebook Part B.')

d.H3('Important: agent and company are IDs, not quantities')
d.P('<b>agent</b> has 333 distinct values and <b>company</b> has 352. They are <i>identifiers</i> (like a roll number), not '
    'measurements. The average of agent 9 and agent 229 is meaningless. Two consequences: we must treat them as '
    'categories, and we must <b>not</b> fill missing values with the mean (which would invent a non-existent agent number).')

d.H3('Hidden missing values: "Undefined"')
d.P('pandas counts only true blanks. A text value such as <b>Undefined</b> is present in the file but means "unknown" - a '
    '<b>disguised missing value</b>. We scanned every text column and found them:')
d.table([
    ['Column', 'Rows with "Undefined"', 'Comment'],
    ['meal', '1,169', 'Codes in the data: BB 92,310 | HB 14,463 | SC 10,650 | Undefined 1,169 | FB 798. '
                      'The dataset documentation says Undefined and SC both mean "no meal package", so they may be merged later (decision for the preprocessing step).'],
    ['market_segment', '2', 'Tiny. Likely safe to treat as missing or fold into the most common group.'],
    ['distribution_channel', '5', 'Tiny, same treatment.'],
], [38 * mm, 36 * mm, 100 * mm])

# ------------------------------------------------------------------ 3
d.H2('3. Numeric summary - what the min and max reveal')
d.P('<b>describe()</b> gives the mean, median (50%), min and max. Impossible or extreme values stand out in min and max '
    'long before any chart. Highlights:')
d.table([
    ['Column', 'Min', 'Median', 'Mean', 'Max', 'What to notice'],
    ['lead_time', '0', '69', '104.0', '737', 'Mean well above median: a long right tail of far-ahead bookings.'],
    ['adr', '-6.38', '94.58', '101.83', '5400', 'A NEGATIVE price and a price of 5,400 per night. Both need investigation.'],
    ['adults', '0', '2', '1.86', '55', 'Rows with zero adults; 55 adults in one booking is not a normal stay.'],
    ['children', '0', '0', '0.10', '10', '4 missing values.'],
    ['babies', '0', '0', '0.01', '10', '10 babies in one booking looks like an error.'],
    ['stays_in_weekend_nights', '0', '1', '0.93', '19', 'Long stays exist.'],
    ['stays_in_week_nights', '0', '2', '2.50', '50', '50 weeknights is unusual.'],
    ['days_in_waiting_list', '0', '0', '2.32', '391', 'Almost always 0, a few huge values.'],
    ['previous_cancellations', '0', '0', '0.09', '26', 'Mostly 0, heavy tail.'],
], [38 * mm, 14 * mm, 16 * mm, 16 * mm, 14 * mm, 76 * mm])
d.NT('<b>Mean vs median:</b> when the mean is noticeably larger than the median, a few very large values are pulling it up '
     '(a right-skewed column). The median is robust to outliers; the mean is not. We will use this idea again in preprocessing '
     'and when we choose the regression metric.')
d.P('These oddities (negative or huge adr, zero adults, zero-night stays) are queued for <b>Step 3: Data Quality</b>. '
    'We only note them here.')

# ------------------------------------------------------------------ 4
d.H2('4. Leakage audit - with evidence')
d.P('<b>The test applied to every column:</b> "At the moment the booking is made (when we would run the prediction), '
    'would I really know this value?" If the answer is no, it cannot be a feature. We tested the suspects with data.')

d.H3('4.1 reservation_status is the answer written in words')
d.table([
    ['reservation_status', 'is_canceled = 0', 'is_canceled = 1', 'Total'],
    ['Canceled', '0', '43,017', '43,017'],
    ['Check-Out', '75,166', '0', '75,166'],
    ['No-Show', '0', '1,207', '1,207'],
    ['Total', '75,166', '44,224', '119,390'],
], [50 * mm, 40 * mm, 40 * mm, 44 * mm])
d.P('The cross-table is perfectly clean: Check-Out is always 0; Canceled and No-Show are always 1. Knowing '
    'reservation_status gives a 100% correct answer, which is exactly why it must be excluded.')
d.NT('<b>New fact we did not have before:</b> in <font face="Courier">is_canceled</font>, <b>No-Show counts as cancelled</b> '
     '(1,207 rows, about 1%). So the target means "the room was not used by this guest", not strictly "the guest clicked cancel". '
     'We keep this definition in mind when we explain the project. (Our Step 1 PDF said the status says "Canceled" for exactly the '
     'rows where is_canceled = 1; the precise statement is "Canceled or No-Show". That sentence is corrected.)')

d.H3('4.2 reservation_status_date: a date that exists only because the outcome already happened')
d.P('<b>What the column is:</b> the date on which the reservation_status was last updated. That is the key. The date is not '
    'something the guest chooses when booking; the hotel system stamps it <i>when the outcome happens</i>.')
d.P('<b>Two bookings, both for arrival on 25 Dec 2016, 3 nights, booked on 1 March 2016:</b>')
d.table([
    ['', 'Booking A', 'Booking B'],
    ['What happens', 'Guest cancels on 30 Oct 2016', 'Guest stays and leaves on 28 Dec 2016'],
    ['reservation_status', 'Canceled', 'Check-Out'],
    ['reservation_status_date', '2016-10-30 (BEFORE the arrival date)', '2016-12-28 (AFTER arrival; = departure date)'],
    ['Did this date exist on 1 March, when we would predict?', 'NO - created on 30 Oct', 'NO - created on 28 Dec'],
], [52 * mm, 61 * mm, 61 * mm])
d.P('<b>Why this leaks the answer:</b> put the status date next to the arrival date. If the status date is <i>before or on</i> '
    'the arrival date, the booking was cancelled (a cancellation always happens before the guest would have arrived). If it is '
    '<i>after</i> arrival, the guest stayed. A model can read the answer straight off these two columns without learning anything about guests.')
d.P('<b>We tested this with a one-line rule and no machine learning:</b> "if reservation_status_date minus arrival date is 0 or '
    'negative, predict cancelled; otherwise predict not cancelled".')
d.table([
    ['Method', 'Accuracy'],
    ['Always predict "not cancelled" (baseline)', '62.96%'],
    ['The one-line date rule (no model at all)', '<b>99.41%</b>'],
], [110 * mm, 64 * mm])
d.P('A rule you can write in one line gets 99.41%. In real use at booking time, the date would not exist, so the deployed model could '
    'not use it and would collapse to a far lower accuracy. That gap between test score and real-life score is exactly what leakage causes.')
d.P('<b>The supporting facts from the data:</b>')
d.B(['For <b>Check-Out</b> rows the status date equals the departure date (arrival + nights) in <b>99.96%</b> of rows - recorded after the stay.',
     'For <b>Canceled</b> rows the date is before arrival in <b>97.95%</b> of rows; median <b>56 days before arrival</b>. It is literally the cancellation date.'])
d.NT('<b>Everyday analogy:</b> predicting whether a parcel was delivered by looking at the "delivered on" stamp. The stamp exists only because '
     'delivery happened, so using it to predict delivery is circular. Verdict: <b>LEAKAGE</b>.')

d.H3('4.3 assigned_room_type: a strong signal that is still leakage')
d.P('We compared reserved_room_type with assigned_room_type. When they differ ("room changed"), the cancellation rate collapses:')
d.table([
    ['Group', 'Rows', 'Cancellation rate'],
    ['Room not changed', '104,473', '41.56%'],
    ['Room changed', '14,917', '5.38%'],
], [70 * mm, 50 * mm, 54 * mm])
d.P('<b>Why this is leakage - the mechanism:</b> the hotel assigns the actual room when the guest <i>arrives</i>. A booking that '
    'is cancelled never reaches check-in, so its assigned room simply stays equal to the reserved one. A changed room therefore '
    'almost proves the guest showed up. The model would learn "room changed means not cancelled", but at booking time that '
    'information does not exist yet.')
d.P('<b>Honest note on strength:</b> this is a <i>partial</i> leak. Only about 12.5% of bookings have a changed room, so on its own the "room changed" '
    'column scores a modest ROC-AUC of 0.585. We exclude it because of <i>when and why</i> the value is created (timing and mechanism), not because it is overwhelmingly strong.')
d.NT('<b>Signal is not the same as leakage.</b> A huge gap in cancellation rate only says the column is <i>related</i> to the target. '
     'What makes it leakage is <b>timing</b> (or that it encodes the outcome). Always ask when the value becomes known.')

d.figure(FIG / 'step2_suspect_cancel_rates.svg', 150,
         'Chart 2 - Cancellation rate by group for the leakage suspects (dashed line = overall 37.04%). Source: notebook E4.')

d.H3('4.4 The suspects we cannot decide by logic alone')
d.table([
    ['Column / group', 'Rows', 'Cancellation rate', 'Reading'],
    ['booking_changes = 0', '101,314', '40.85%', 'Most bookings never change.'],
    ['booking_changes = 1', '12,701', '14.23%', 'Changed bookings cancel far less.'],
    ['booking_changes = 2', '3,805', '20.13%', ''],
    ['booking_changes = 3 or more', '1,570', '16.56%', ''],
    ['days_in_waiting_list = 0', '115,692', '36.19%', ''],
    ['days_in_waiting_list > 0', '3,698', '63.79%', 'Waiting-list bookings cancel much more.'],
], [56 * mm, 24 * mm, 34 * mm, 60 * mm])
d.B(['<b>booking_changes</b> is the <i>final</i> count. At the moment of booking it is always 0. Changes happen later, and a guest who '
     'cancels early has little time to change anything. So the final count partly reflects the outcome. Verdict: leakage suspect.',
     '<b>days_in_waiting_list</b> is known only after the waiting period ends, so the timing is borderline. It is a real '
     'operational feature if the prediction is run at confirmation time, but not at the instant of booking.',
     'We will not drop them blindly. In the <b>ablation experiments</b> we train with and without each one and explain the score change.'])

d.H3('4.5 A counter-intuitive pattern: deposit_type')
d.table([
    ['deposit_type', 'Rows', 'Cancellation rate'],
    ['No Deposit', '104,641', '28.38%'],
    ['Non Refund', '14,587', '99.36%'],
    ['Refundable', '162', '22.22%'],
], [70 * mm, 50 * mm, 54 * mm])
d.P('Common sense says a guest who paid a non-refundable deposit would be <i>less</i> likely to cancel. The data says '
    'the opposite: 99.36% cancel. We do not know the reason yet and we will not invent one. Possible directions to investigate in EDA: '
    'the hotel, the year, the market segment and the country of those bookings, and whether this is how the hotel records '
    'cancelled bookings. Until explained, this column is <b>NEEDS CARE</b>: very strong, but we must understand it before trusting it.')

d.H3('4.6 Second pass: a data-driven re-audit of all 31 columns')
d.P('Judging by logic alone can miss something. So we added a second method. <b>Single-column screen:</b> for each column we trained a tiny decision tree '
    '(depth 5) that sees <i>only that column</i> and measured cross-validated <b>ROC-AUC</b> (5 folds). ROC-AUC is 0.5 for random guessing and 1.0 for perfect '
    'prediction (the full definition comes in the metrics PDF). A column that alone gets a near-perfect score is almost certainly leaking.')
d.figure(FIG / 'step2_single_feature_auc.svg', 150,
         'Chart 3 - Single-column ROC-AUC for all 31 columns (dashed line = random guessing). Source: notebook Part F.')
d.table([
    ['Column', 'Single-column AUC', 'Comment'],
    ['reservation_status', '1.0000', 'Perfect: the screen catches this one immediately.'],
    ['country', '0.6954', 'Legitimate: where the guest comes from is known at booking.'],
    ['lead_time', '0.6905', 'Legitimate: known at booking.'],
    ['deposit_type', '0.6634', 'Strong because of the Non Refund oddity (see 4.5).'],
    ['reservation_status_date', '0.6381', 'LOW - yet we proved it leaks (see below).'],
    ['total_of_special_requests', '0.6355', 'Moderate; timing suspect.'],
    ['assigned_room_type', '0.6023', 'Low alone; leak is partial (see 4.3).'],
    ['all other columns', '0.50 - 0.63', 'Weak alone. No other column leaks perfectly by itself.'],
], [52 * mm, 34 * mm, 88 * mm])

d.H3('The blind spot of the screen: leakage hidden between two columns')
d.P('The screen scored reservation_status_date at only 0.638. Does that make it safe? No. The leak appears when it is <i>combined</i> with the arrival date. '
    'We built <font face="Courier">gap = status_date - arrival_date</font> and ran the same screen:')
d.table([
    ['Derived column', 'AUC', 'Reading'],
    ['gap (status date minus arrival date)', '<b>0.9998</b>', 'Near perfect - the date leak lives in the relationship between two columns.'],
    ['room_changed (reserved room != assigned room)', '0.5848', 'Modest strength (partial leak), excluded for timing and mechanism.'],
], [64 * mm, 20 * mm, 90 * mm])
d.NT('<b>Lesson:</b> a low single-column score does not prove a column is safe. Leakage can hide in combinations of columns. '
     'That is why we use <b>two methods together</b>: (1) timing logic ("when is this value created?") and (2) data screens.')

d.H3('A new leak found in the re-audit: required_car_parking_spaces')
d.table([
    ['Parking spaces required', 'Rows', 'Cancellation rate'],
    ['0', '111,974', '39.49%'],
    ['1', '7,383', '<b>0.00%</b>'],
    ['2 or more', '33', '<b>0.00%</b>'],
], [70 * mm, 50 * mm, 54 * mm])
d.P('Out of 7,416 bookings that required parking, <b>not a single one was cancelled</b>. Real human behaviour never produces exactly zero. The explanation is the '
    'same kind as with the room: parking is recorded only for guests who actually arrive. A cancelled booking never gets a parking record, so it stays at 0. '
    'In my first pass I marked this column "needs care", which was too lenient; the data corrected me. Verdict: <b>LEAKAGE</b>.')
d.NT('<b>A reusable trick:</b> look for groups with a cancellation rate of exactly 0% or 100% and enough rows. A perfect group in real-world behaviour '
     'almost always means the column is recorded after the outcome.')

d.H3('Remaining columns checked')
d.table([
    ['Check', 'Result', 'Reading'],
    ['total_of_special_requests', '0 requests: 47.72% cancel | 1: 22.02% | 2: 22.10% | 3+: 16.82%',
     'Gradual pattern, not a perfect split. Requests can be added after booking, so timing is suspect: kept as NEEDS CARE and settled by ablation.'],
    ['previous_cancellations', 'Any previous cancellation: 91.64% cancel (6,484 rows) vs 33.91%',
     'Very strong but legitimate: guest history is known before this booking, and past behaviour predicts future behaviour.'],
    ['is_repeated_guest', 'Repeated guests: 14.49% cancel vs 37.79%', 'Legitimate and plausible.'],
    ['adr = 0 share', '2.32% of non-cancelled vs 0.48% of cancelled', 'Zero-price rows are mostly stays that happened (Step 3 will explain them). No leakage signal.'],
    ['mean adr', 'Non-cancelled 99.99 | Cancelled 104.96', 'Similar; adr is quoted at booking. Fine to use (outliers handled in Step 3).'],
], [40 * mm, 62 * mm, 72 * mm])

d.H3('Is the audit complete?')
d.P('All 31 non-target columns have now been examined by both methods. Final leakage list: <b>reservation_status, reservation_status_date, assigned_room_type, '
    'required_car_parking_spaces</b>. Suspects settled later by ablation: <b>booking_changes, days_in_waiting_list, total_of_special_requests</b>. '
    '<b>Honest limit:</b> an audit can find leakage but can never prove there is none. Two more safeguards remain: the ablation experiments, and a rule for the '
    'final model - if its score looks too good to be true, investigate before celebrating.')

# ------------------------------------------------------------------ 5
d.H2('5. The data dictionary - all 32 columns')
d.P('Verdict colours: green = USABLE, yellow = NEEDS CARE, red = LEAKAGE, blue = TARGET. '
    f'Totals: {(dic.verdict == "USABLE").sum()} usable, {(dic.verdict == "NEEDS CARE").sum()} need care, '
    f'{(dic.verdict == "LEAKAGE").sum()} leakage, {(dic.verdict == "TARGET").sum()} target.')
rows = [['Column (type)', 'Missing', 'Unique', 'Verdict', 'Reason']]
for _, r in dic.iterrows():
    rows.append([f'<b>{r["column"]}</b><br/>{r["dtype"]}', f'{int(r["missing"]):,}', f'{int(r["n_unique"]):,}', r['verdict'], r['reason']])
d.table(rows, [47 * mm, 17 * mm, 16 * mm, 20 * mm, 74 * mm], verdict_col=3)
d.NT('<b>Remember:</b> these verdicts are our current judgment. NEEDS CARE does not mean "bad" - it means "a decision is required, and '
     'we must be able to defend it". Every such decision will be recorded with its reason in the preprocessing step.')

# ------------------------------------------------------------------ 6
d.H2('6. Interview questions from this step (with model answers)')
d.qa([
 ('What is data leakage and how did you detect it in your project?',
  'Leakage is when a feature contains information that would not be available at prediction time or that directly encodes the target. '
  'I applied a timing test to each column: "would I know this at booking time?" I confirmed it with data: a cross-table showed reservation_status '
  'maps exactly onto is_canceled, and reservation_status_date equals the departure date on 99.96% of check-outs.'),
 ('assigned_room_type is strongly related to cancellation. Why not keep it - it makes the model better?',
  'It makes the model better in testing only. The room is assigned at check-in, so a changed room almost proves the guest arrived '
  '(5.4% cancel vs 41.6%). A cancelled booking never reaches check-in. At booking time the value does not exist, so the deployed model would '
  'lose that signal and perform much worse than the test score promised.'),
 ('Is every feature that is strongly related to the target leakage?',
  'No. A strong relationship is a signal; leakage is about timing or encoding the outcome. lead_time is strongly related to cancellation and is '
  'perfectly legitimate because it is known at booking. The question is always "when is this value known?"'),
 ('Explain why reservation_status_date leaks the target.',
  'The date is stamped by the hotel system when the outcome happens: the cancellation date for cancelled bookings, the departure date for stays. Compared with the arrival date, '
  '"on or before arrival" means cancelled and "after arrival" means stayed. A one-line rule on that difference scores 99.41% accuracy with no model, but at booking time the date does not exist yet.'),
 ('You ran a single-column leakage screen and reservation_status_date scored only 0.64 AUC. Is it safe?',
  'No. Leakage can hide in the relationship between columns. Combined with arrival date as a gap, the AUC is 0.9998. A single-column screen finds obvious leaks (like reservation_status at 1.0) '
  'but not those that need a second column, so I use timing logic together with data screens.'),
 ('How can you spot leakage in a feature like required_car_parking_spaces?',
  'Look for groups with a cancellation rate of exactly 0% or 100% that have many rows. All 7,416 bookings with parking had 0 cancellations, which real behaviour does not produce. '
  'It means the value is recorded only for guests who arrive, so it exists only after the outcome.'),
 ('Can you prove a dataset has no leakage left?',
  'No. An audit can only find leakage. I reduce the risk with timing logic for every column, data screens, ablation experiments, and a sanity rule: if the final score looks too good to be true, investigate.'),
 ('deposit_type "Non Refund" has a 99% cancellation rate. What do you do?',
  'I would not trust it or drop it blindly. I would first investigate by hotel, year, market segment and country to find out whether it is a real '
  'behaviour or a recording artifact, then run ablation (with vs without) and explain the score change. Decide only after I can explain it.'),
 ('agent and company have missing values. Would you fill them with the mean?',
  'No. They are IDs, so a mean has no meaning and invents a fake agent. I would treat them as categories; missing can be its own category '
  '(it likely means "no agent / no company"). For company at 94% missing, a has-company flag or dropping it is reasonable.'),
 ('What is a disguised missing value? Give an example from this data.',
  'A value present in the file that really means "unknown", such as the text "Undefined" in meal (1,169 rows), market_segment (2) and '
  'distribution_channel (5). pandas does not count them as missing, so you must scan the category values to find them.'),
 ('Why are mean and median of adr different, and what does that tell you?',
  'Mean 101.83 vs median 94.58, with a maximum of 5,400. A few extreme prices pull the mean up. It signals right skew and outliers, and that '
  'the median or a robust metric may describe typical behaviour better.'),
 ('Your target includes No-Show as cancelled. Is that correct?',
  'It is a definition choice: 1,207 rows (about 1%). From a hotel point of view a no-show also leaves the room unused, so grouping makes sense, '
  'but it must be stated clearly. If the business cared about early cancellations only, we would define the target differently.'),
 ('What is cardinality and why does country (177 values) cause trouble?',
  'Cardinality is the number of distinct values in a column. One-hot encoding 177 countries creates 177 sparse columns. Common options: group rare '
  'countries into "Other", or use frequency/target encoding (carefully, to avoid leakage).'),
])

# ------------------------------------------------------------------ 7
d.H2('7. Self-check (answer in your own words before Step 3)')
d.B(['In your own words, with the two example bookings (A and B), why does reservation_status_date reveal the answer?',
     'Why did the single-column screen give reservation_status_date a low score, and what does that teach you?',
     'Why is required_car_parking_spaces leakage? What number in the table gave it away?',
     'Why is assigned_room_type leakage even though it predicts cancellation so well? Explain the mechanism, not just "it is known later".',
     'What is the difference between a strong signal and leakage? Give one example of each from this data.',
     'Why must agent and company not be filled with the mean?',
     'What does "Undefined" in the meal column mean for missing-value counts?',
     'The target includes No-Show. Why might that matter to the hotel?',
     'booking_changes is not proven leakage. How will we decide whether to keep it?'])

d.H2('What comes next: STEP 3 - Data Quality')
d.P('We investigate the oddities noted here, with counts and reasons for every decision: adr negative or huge and adr = 0, '
    'zero-adult and zero-guest bookings, zero-night stays, extreme lead times, and duplicate rows. We decide what to keep, '
    'fix, flag or remove, and write each decision down.')

out = FOLDER / 'STEP_2_Data_Dictionary_And_Leakage.pdf'
d.build(out, 'STEP 2 - Data Dictionary and Leakage Audit', 'Hotel Booking Cancellation ML | STEP 2 - Data Dictionary and Leakage Audit')
print('written', out)
