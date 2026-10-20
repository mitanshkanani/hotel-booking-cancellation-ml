"""Builds STEP_3_Data_Quality.pdf from the executed notebook outputs and CSVs.

Run from anywhere:  python data_exploration/STEP_3_Data_Quality/builders/build_step3_pdf.py
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib.units import mm

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '_shared'))
from pdf_common import Doc, SMALL  # noqa: E402

FOLDER = Path(__file__).resolve().parent.parent
FIG = FOLDER / 'figures'
dec = pd.read_csv(FOLDER / 'STEP_3_quality_decisions.csv')
rem = pd.read_csv(FOLDER / 'STEP_3_row_removal_log.csv')

d = Doc()
d.H1('STEP 3 - Data Quality')
d.P('Hotel Booking Cancellation Project | Data Exploration series', SMALL)
d.SP(4)
d.NT('<b>What this PDF is:</b> the investigation of every oddity found in Steps 1 and 2 (duplicates, zero-guest bookings, zero-night stays, '
     'bad prices, extreme values). For each one we look at the evidence, then decide: <b>drop, fix, flag or keep</b>, and write the reason down. '
     'All numbers come from <b>STEP_3_data_quality.ipynb</b> in this folder.')

d.H2('Files for this step')
d.table([
    ['File', 'What it is'],
    ['STEP_3_data_quality.ipynb', 'The notebook that produced every number and chart (run top to bottom).'],
    ['STEP_3_row_removal_log.csv', 'How many rows each cleaning rule removed.'],
    ['STEP_3_quality_decisions.csv', 'The full decision table (issue, rows, decision, reason, where applied).'],
    ['figures/step3_adr_distribution.svg', 'Chart 1: distribution of adr (price per night).'],
    ['figures/step3_rows_removed_per_rule.svg', 'Chart 2: rows removed by each rule.'],
    ['../../data/hotel_bookings_clean_v1.csv', 'The cleaned dataset (118,544 rows). It lives in data/, which is git-ignored.'],
], [70 * mm, 104 * mm])

d.H2('Libraries used in this step')
d.table([
    ['Library', 'Version', 'Why we use it here'],
    ['pandas', '2.3.3', 'duplicated(), groupby, crosstab, quantile, boolean masks to find and count problem rows; writes the cleaned CSV.'],
    ['numpy', '2.5.2', 'Array helpers for the chart positions.'],
    ['matplotlib', '3.11.1', 'The two charts, saved as SVG only.'],
    ['nbformat + nbclient', '5.11.1 / 0.11.0', 'Build and execute the notebook.'],
    ['svglib + reportlab', '2.3.0 / 5.0.1', 'Put the SVG charts into this PDF.'],
], [34 * mm, 30 * mm, 110 * mm])

# ------------------------------------------------------------------ 1
d.H2('1. Why data quality comes before EDA and models')
d.P('Averages, correlations and models are all computed from the rows we give them. A few impossible rows (a negative price, 55 adults in one room) '
    'can bend an average or a correlation, and a model will happily learn from them. So we first find out what is broken.')
d.P('For every oddity we ask three questions, in this order:')
d.B(['<b>Is it an error?</b> (impossible: negative price, a booking with nobody in it) -> usually drop or fix.',
     '<b>Is it rare but real?</b> (a 2-year lead time, a 30-night stay) -> keep; it is true behaviour.',
     '<b>Is it an outlier that is real but extreme?</b> (a very expensive night) -> keep, but later choose methods that are not wrecked by it.'])
d.NT('<b>Golden rule of this step: define removal rules by the VALUES, never by the outcome.</b> We never remove rows because they were cancelled or not. '
     'Removing rows based on the target would make the model look better than it really is, which is a form of cheating. Every rule below is '
     'about impossible or meaningless values.')

# ------------------------------------------------------------------ 2
d.H2('2. Duplicate rows')
d.P('A <b>duplicate</b> is a row identical to an earlier row in all 32 columns.')
d.table([
    ['Measure', 'Value'],
    ['Rows that are a 2nd or later copy of an earlier row', '31,994 (26.80% of the data)'],
    ['Rows belonging to any duplicate group (all copies counted)', '40,165'],
    ['Number of distinct duplicate groups', '8,171'],
    ['Cancellation rate - rows in duplicate groups', '58.39%'],
    ['Cancellation rate - unique rows', '26.22%'],
], [110 * mm, 64 * mm])
d.P('Group sizes: most groups have 2 copies (5,034 groups), then 3 copies (969), 4 copies (497), and so on, with a long tail of larger groups.')
d.P('<b>Where do they come from?</b> The share of rows inside a duplicate group varies hugely by market segment:')
d.table([
    ['Market segment', 'Share of its rows in a duplicate group'],
    ['Groups', '84.4%'],
    ['Offline TA/TO (travel agents / tour operators)', '50.4%'],
    ['Corporate', '27.8%'],
    ['Online TA', '14.6%'],
    ['Direct', '11.1%'],
    ['Complementary', '10.1%'],
    ['Aviation', '8.0%'],
], [110 * mm, 64 * mm])
d.P('<b>The six biggest duplicate groups, shown as real rows:</b>')
d.table([
    ['Copies', 'Hotel', 'Segment', 'Lead time', 'Arrival', 'Adults', 'Nights', 'adr', 'Cancelled'],
    ['180', 'City', 'Groups', '277', '7 Nov 2016', '2', '3', '100.0', 'yes'],
    ['150', 'City', 'Groups', '68', '17 Feb 2016', '2', '2', '75.0', 'yes'],
    ['109', 'City', 'Offline TA/TO', '188', '15 Jun 2016', '1', '2', '130.0', 'yes'],
    ['101', 'City', 'Groups', '158', '24 May 2016', '1', '2', '130.0', 'yes'],
    ['100', 'City', 'Offline TA/TO', '34', '8 Dec 2015', '1', '2', '90.0', 'yes'],
    ['99', 'City', 'Groups', '156', '26 Apr 2017', '2', '3', '100.0', 'yes'],
], [16 * mm, 14 * mm, 28 * mm, 18 * mm, 26 * mm, 15 * mm, 15 * mm, 15 * mm, 20 * mm])
d.P('Each big group is one organisation (a tour group or agency) booking, say, 180 identical rooms for the same dates, and then cancelling all of '
    'them together. <b>Every one of the six biggest groups was cancelled completely.</b> That explains the 58% vs 26% gap: group bookings are made in '
    'batches and they cancel in batches.')

d.H3('Keep or drop duplicates? Our decision: KEEP, but split the data carefully')
d.P('<b>Why not drop them:</b> these look like real separate bookings. Dropping 31,994 rows would erase real group behaviour and change the data we are trying to model.')
d.P('<b>The danger of keeping them: leakage across the train/test split.</b> A simple example: a group of 100 identical bookings. If 80 randomly land in the training set and '
    '20 in the test set, the model has already memorised that exact booking pattern, so the test score looks great without proving anything. '
    'The fix is a <b>group-aware split</b>: all bookings with identical features go to the same side (all train or all test). We apply it in Step 6. '
    'We will also repeat one experiment with duplicates dropped, to see how much they change the score (a sensitivity test).')

d.H3('Label noise: identical features, different outcomes')
d.P('After removing the four leakage columns, we grouped bookings with identical features: 85,688 groups. <b>289 groups contain both outcomes</b> '
    '(some cancelled, some not) covering 2,107 rows, about 1.8% of the data. The model sees identical inputs and must give one answer, so it will be wrong '
    'for some of them whatever we do. This is <b>irreducible error</b> (label noise) and it puts a ceiling on how good any model can be. Remember it when judging scores.')

# ------------------------------------------------------------------ 3
d.H2('3. Zero-guest bookings')
d.P('<font face="Courier">total_guests = adults + children + babies</font>. A booking with zero guests is not a person staying in a room.')
d.table([
    ['Measure', 'Value'],
    ['Rows with zero guests', '180 (0.15% of the data)'],
    ['Cancellation rate', '13.89%'],
    ['Hotel', 'City 167, Resort 13'],
    ['reservation_status', 'Check-Out 155, Canceled 24, No-Show 1'],
    ['adr', 'median 0.00, mean 10.46, max 200 (most are exactly 0)'],
    ['Nights stayed', 'median 2, mean 4.52, up to 57'],
], [70 * mm, 104 * mm])
d.P('Most have a price of zero yet many are recorded as completed stays of several nights, so these are not normal paying guests. '
    '<b>Decision: DROP all 180.</b> They are impossible as guest stays and are only 0.15% of the data, so dropping loses nothing.')
d.P('A separate group: <b>403 rows have zero adults</b>, and 223 of them still list children or babies. Children travelling alone is odd, but it is only 0.19% of rows and '
    'could be a recording habit. <b>Decision: KEEP</b>, and revisit if errors concentrate there.')

# ------------------------------------------------------------------ 4
d.H2('4. Zero-night stays')
d.P('<font face="Courier">total_nights = stays_in_weekend_nights + stays_in_week_nights</font>.')
d.table([
    ['Measure', 'Value'],
    ['Rows with zero nights', '715 (0.60% of the data)'],
    ['Cancellation rate', '4.9% (far below the overall 37%)'],
    ['reservation_status', 'Check-Out 680, Canceled 22, No-Show 13'],
    ['Hotel', 'Resort 384, City 331'],
    ['adr', '<b>exactly 0 in all 715 rows</b>'],
    ['Overlap with zero-guest rows', '70 rows'],
], [70 * mm, 104 * mm])
d.P('<b>The key observation: all 715 zero-night rows have adr = 0.</b> Remember that adr = total room revenue / number of nights. With 0 nights that division '
    'is 0 / 0, which is undefined. The system most likely stored 0. So the zero is not "a free stay"; it is a price that <i>cannot be calculated</i>. '
    '(This is consistent with the data, though the data cannot prove the hotel system\'s internals.)')
d.P('<b>Decision: DROP all 715.</b> They are not overnight stays, the price is undefined, and their very different cancellation rate (4.9%) would teach the model a pattern '
    'that belongs to a recording quirk, not to guest behaviour.')
d.NT('<b>Deployment note for later:</b> because the model never saw zero-night bookings, the deployed service should reject or flag a booking with 0 nights instead of '
     'predicting on it (input validation). We will add this in Step 10.')

# ------------------------------------------------------------------ 5
d.H2('5. adr problems: negative, zero and extreme')
d.H3('5.1 Negative adr: one row')
d.P('One row has adr = -6.38 (Resort Hotel, Groups, 10 nights, checked out). A price cannot be negative (a refund or a data error). '
    '<b>Decision: DROP</b> (1 row).')
d.H3('5.2 adr = 0: 1,959 rows')
d.P('1,959 rows (1.64%) have adr exactly 0. Of these, 715 are the zero-night rows we already explained. The rest:')
d.table([
    ['Market segment', 'Rows with adr = 0', 'Segment size', 'Share of segment with adr = 0'],
    ['Complementary', '680', '743', '<b>91.5%</b>'],
    ['Online TA', '367', '56,477', '0.6%'],
    ['Offline TA/TO', '332', '24,219', '1.4%'],
    ['Groups', '252', '19,811', '1.3%'],
    ['Direct', '240', '12,606', '1.9%'],
    ['Corporate', '82', '5,295', '1.5%'],
    ['Aviation', '6', '237', '2.5%'],
], [40 * mm, 40 * mm, 40 * mm, 54 * mm])
d.P('For the <b>Complementary</b> segment, adr = 0 is by design: these are free stays. For the other segments, zeros are rare (about 1-2%) and unexplained '
    '(free upgrades, staff, mistakes). <b>Decision:</b> keep them for the cancellation model, because they are real bookings with real cancellation behaviour. '
    'But for the <b>adr regression</b>, a price of 0 is not a price, so regression uses only rows with adr &gt; 0.')
d.H3('5.3 Extreme adr: the 5400 row')
d.table([
    ['adr quantile', 'Value'],
    ['Median (50%)', '94.58'],
    ['90%', '164.00'],
    ['99%', '252.00'],
    ['99.9%', '326.20'],
    ['99.99%', '388.00'],
    ['Maximum', '<b>5400.00</b>'],
], [70 * mm, 104 * mm])
d.figure(FIG / 'step3_adr_distribution.svg', 140,
         'Chart 1 - adr distribution (clipped at the 99.5th percentile for display; the true maximum is 5,400). Source: notebook Part D.')
d.P('The top values are 5,400 (City Hotel, Offline TA/TO, 1 night, 2 adults, cancelled), then 510, 508, 451.5, 450 and 437. The 5,400 is more than ten times the next value and '
    'far beyond the 99.99th percentile of 388: almost certainly an entry error. <b>Decision: DROP</b> (1 row). The next ones (510, 508) are plausible peak or suite '
    'prices for one night, so we <b>keep</b> them, along with the other 275 rows between 300 and 1,000.')
d.NT('<b>Why one row matters:</b> for the regression task, a single 5,400 among 117,000 values would pull the mean up and dominate any squared-error metric (RMSE squares the error, so one '
     'huge error counts enormously). The median is barely affected. This is a concrete reason for MAE vs RMSE discussions later.')

# ------------------------------------------------------------------ 6
d.H2('6. Other extreme values')
d.table([
    ['Column', 'Median', '99th pct', '99.9th pct', 'Max'],
    ['lead_time', '69', '444', '605', '737'],
    ['adults', '2', '3', '3', '55'],
    ['children', '0', '2', '2', '10'],
    ['babies', '0', '0', '1', '10'],
    ['total_nights', '3', '14', '25', '69'],
    ['days_in_waiting_list', '0', '75', '231', '391'],
    ['previous_cancellations', '0', '1', '14', '26'],
    ['previous_bookings_not_canceled', '0', '3', '22', '72'],
    ['booking_changes', '0', '3', '6', '21'],
], [64 * mm, 22 * mm, 28 * mm, 30 * mm, 30 * mm])
d.P('When the maximum is far above the 99.9th percentile (adults 55 vs 3, babies 10 vs 1, children 10 vs 2), a handful of rows are extreme. Then we count rows beyond sensible limits:')
d.table([
    ['Rule', 'Rows', 'Cancel rate', 'Mean adr', 'Decision'],
    ['adults &gt;= 5', '16', '100%', '0.00', 'DROP'],
    ['children &gt;= 4', '1', '100%', '133.16', 'DROP'],
    ['babies &gt;= 3', '2', '0%', '89.72', 'DROP'],
    ['total_nights &gt;= 15', '439', '55.35%', '78.31', 'KEEP (long stays are real)'],
    ['lead_time &gt;= 500', '481', '85.65%', '67.57', 'KEEP (real and a strong signal)'],
    ['days_in_waiting_list &gt;= 200', '227', '48.46%', '77.26', 'KEEP (column excluded anyway)'],
], [50 * mm, 16 * mm, 26 * mm, 24 * mm, 58 * mm])
d.P('<b>The 16 rows with 5 or more adults</b> have 5, 6, 10, 20, 26, 27, 40, 50 and 55 adults. All 16 are Resort Hotel, all are cancelled, all have adr = 0, and they sit close '
    'together near the start of the file. They look like placeholder or test records, not guests. If we kept them, the model would learn "many adults means cancelled" from 16 strange rows. '
    '<b>Decision: DROP.</b> The three rows with 10 children, 10 babies and 9 babies are implausible counts, so <b>DROP</b> them too.')
d.P('<b>Kept on purpose:</b> lead times of 500+ days (only 481 rows, but 85.65% cancel, a real and strong pattern) and stays of 15+ nights. '
    'We may transform lead_time (for example log) for linear models in Step 6.')

# ------------------------------------------------------------------ 7
d.H2('7. The cleaning result: dataset v1')
rows = [['Rule', 'Rows flagged', 'Additional unique rows removed']]
for _, r in rem.iterrows():
    rows.append([escape(str(r['rule'])), f'{int(r["rows_flagged"]):,}', f'{int(r["additional_unique_rows_removed"]):,}'])
rows.append(['<b>Total removed</b>', '', '<b>846 (0.71% of 119,390)</b>'])
d.table(rows, [88 * mm, 40 * mm, 46 * mm])
d.figure(FIG / 'step3_rows_removed_per_rule.svg', 140, 'Chart 2 - Rows removed by each rule. Source: notebook Part G.')
d.P('Notice that "zero nights" flags 715 rows but removes only 645 additional ones: 70 were already removed by the zero-guest rule. The rules overlap, so we count unique rows.')
d.B(['<b>Result:</b> 118,544 rows x 32 columns, saved as <font face="Courier">data/hotel_bookings_clean_v1.csv</font>.',
     '<b>Cancellation rate</b> moved from 37.04% to <b>37.25%</b>. The removed rows cancelled only 7.80% of the time (most are zero-night check-outs), which is why removing them nudges the rate up slightly.',
     '<b>Regression rows (adr &gt; 0):</b> 117,395. The 1,149 rows with adr = 0 stay for classification only.',
     'We checked with assertions that no zero-guest, zero-night, negative-adr or adr &gt; 1000 row remains.'])
d.NT('<b>What we did NOT do here:</b> filling missing values, encoding categories, scaling, and handling duplicates in the split. Those must be done in Step 6 <i>after</i> '
     'splitting the data into train and test, using only the training data to learn the fill values. If we computed them on the whole dataset first, information from the test '
     'set would leak into training.')

# ------------------------------------------------------------------ 8
d.H2('8. Full decision table')
d.P('Every issue found, with the decision and where it is applied. "PLAN" means the action happens in Step 6.')
trows = [['Issue', 'Rows', 'Decision', 'Reason', 'Applied in']]
for _, r in dec.iterrows():
    trows.append([escape(str(r['issue'])), f'{int(r["rows"]):,}', f'<b>{escape(str(r["decision"]))}</b>', escape(str(r['reason'])), escape(str(r['applied_in']))])
d.table(trows, [34 * mm, 19 * mm, 30 * mm, 55 * mm, 36 * mm])
d.P('Note: the table counts rows in the raw data, so "adr = 0 with nights &gt; 0" shows 1,244 raw rows; 95 of them were removed by other rules, leaving the 1,149 mentioned above.')

# ------------------------------------------------------------------ 9
d.H2('9. Interview questions from this step (with model answers)')
d.qa([
 ('Your dataset has 27% duplicate rows. Do you drop them?',
  'Not automatically. I check what they are. Here they concentrate in the Groups (84%) and Offline TA/TO (50%) segments, and the biggest groups are 100-180 identical bookings that all cancelled together, '
  'so they look like genuine batch bookings. I keep them but use a group-aware train/test split so identical rows never sit on both sides, and I run a sensitivity test with duplicates dropped.'),
 ('What is the problem with duplicates and a random train/test split?',
  'Copies of the same row can land in both sets, so the model is tested on something it has effectively already seen. The test score is inflated and does not measure generalisation. '
  'This is a leakage problem, not just extra weight.'),
 ('All zero-night bookings have adr = 0. Is that a free stay?',
  'Probably not. adr is revenue divided by nights, and with 0 nights the value is undefined, so a stored 0 is most likely a placeholder. Genuine free stays show up as the Complementary segment, where 91.5% of rows have adr 0 by design. '
  'I dropped the zero-night rows and would add input validation in deployment.'),
 ('How do you decide whether an unusual value is an error or a real outlier?',
  'Ask: is it possible in the real world, is it consistent with other columns, and does it cluster in a suspicious way? A negative price is impossible. 5,400 per night is ten times the next value, so it is an error. '
  'A 600-day lead time is possible and shows a coherent pattern (85% cancel), so it is real. Real extremes are kept; impossible ones are removed.'),
 ('Why must removal rules be based on values and not on the target?',
  'Removing rows because of their label (for example, dropping hard-to-predict cancellations) makes the model look better than it is. The data we clean must be the data the model will face in real life, '
  'where the label is unknown. So rules refer only to impossible or meaningless input values.'),
 ('Why do you wait until after the train/test split to fill missing values?',
  'Fill values (means, medians, most frequent categories) are learned from data. If learned on the full dataset, information from the test set leaks into training. '
  'I split first, learn the fill values from the training part only, and apply them to the test part.'),
 ('289 groups of identical features have both outcomes. What does that mean for your model?',
  'Identical inputs with different outputs cannot all be predicted correctly: it is irreducible error, about 1.8% of rows. It sets a ceiling on achievable performance, so I do not chase a perfect score.'),
 ('Cleaning moved the cancellation rate from 37.04% to 37.25%. Is that a problem?',
  'No. The removed rows (0.71% of data) cancelled only 7.8% of the time, mostly zero-night check-outs, so removing them nudges the rate up slightly. It is a small, explainable change, and the rules were value-based, not label-based.'),
 ('One adr value is 5,400 but most are near 100. Why does that matter for the regression metric?',
  'Squared-error metrics like RMSE give huge weight to one huge error, and a mean is pulled by it. MAE and the median are far less sensitive. After removing the clear error, remaining high prices are still an argument for considering MAE or a log transform.'),
])

# ------------------------------------------------------------------ 10
d.H2('10. Self-check (answer in your own words before Step 4)')
d.B(['Why do we keep the duplicates, and what extra care does that require when splitting the data?',
     'Why is "adr = 0" a free stay for one group of rows but not for the zero-night rows?',
     'Why must a removal rule be about values and not about whether a booking was cancelled?',
     'What is irreducible error, and where did we see it in this step?',
     'Why do we fill missing values only after the train/test split?'])

d.H2('What comes next: STEP 4 - Target Analysis')
d.P('We study the thing we predict: how cancellations vary over time, by hotel and by season, how imbalanced the target is in the cleaned data, '
    'what accuracy a naive model gets, and why that decides which metrics make sense. This prepares the metric discussion (ROC-AUC, precision, recall) for later.')

out = FOLDER / 'STEP_3_Data_Quality.pdf'
d.build(out, 'STEP 3 - Data Quality', 'Hotel Booking Cancellation ML | STEP 3 - Data Quality')
print('written', out)
