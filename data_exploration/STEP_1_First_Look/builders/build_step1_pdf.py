import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Preformatted, PageBreak, KeepTogether)

from pathlib import Path
out = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / 'STEP_1_First_Look_At_The_Data.pdf')

ss = getSampleStyleSheet()
BODY = ParagraphStyle('body', parent=ss['Normal'], fontName='Helvetica', fontSize=10.5, leading=15, spaceAfter=6)
H1 = ParagraphStyle('h1', parent=ss['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=24, spaceAfter=8, textColor=colors.HexColor('#1F3A5F'))
H2 = ParagraphStyle('h2', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor('#1F3A5F'))
H3 = ParagraphStyle('h3', parent=ss['Heading3'], fontName='Helvetica-Bold', fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4)
BUL = ParagraphStyle('bul', parent=BODY, leftIndent=14, bulletIndent=2, spaceAfter=3)
CODE = ParagraphStyle('code', fontName='Courier', fontSize=8.6, leading=11, backColor=colors.HexColor('#F3F4F6'),
                      borderPadding=6, spaceBefore=4, spaceAfter=10, leftIndent=4)
NOTE = ParagraphStyle('note', parent=BODY, backColor=colors.HexColor('#FFF7E0'), borderPadding=6,
                      borderColor=colors.HexColor('#E0B400'), borderWidth=0.6, spaceBefore=6, spaceAfter=10)
SMALL = ParagraphStyle('small', parent=BODY, fontSize=9, leading=12)

story = []
def P(t, s=BODY): story.append(Paragraph(t, s))
def B(items):
    for t in items: story.append(Paragraph(t, BUL, bulletText='-'))
def C(t): story.append(Preformatted(t, CODE))
def NT(t): story.append(Paragraph(t, NOTE))
def SP(h=6): story.append(Spacer(1, h))

def table(data, widths, header=True, fs=9):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), fs),
          ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#B8BEC8')),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
    if header:
        st += [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F3A5F')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')]
    t.setStyle(TableStyle(st))
    story.append(t); SP(8)

def wrap(rows):  # make cells wrap
    cs = ParagraphStyle('c', parent=SMALL, fontSize=8.8, leading=11)
    ch = ParagraphStyle('ch', parent=cs, textColor=colors.white, fontName='Helvetica-Bold')
    return [[Paragraph(str(c), ch if i == 0 else cs) for c in r] for i, r in enumerate(rows)]

# ---------------------------------------------------------------- TITLE
P('STEP 1 - First Look at the Data', H1)
P('Hotel Booking Cancellation Project | Data Exploration series', SMALL)
SP(4)
NT('<b>What this PDF is:</b> a record of the very first thing we did with the data: load the file, check its size, '
   'its column types, a few raw rows, and how balanced the target is. Everything here was actually run on your '
   'machine, and the numbers below are the real outputs. Read it slowly; each section answers "what did we do", '
   '"why did we do it", and "what did we learn".')

P('Libraries used in this step', H2)
table(wrap([
    ['Library', 'Version', 'Why we use it here'],
    ['pandas', '2.3.3', 'Loads the CSV into a DataFrame (a table in memory) and gives us .shape, .dtypes, .head(), .value_counts().'],
    ['numpy', '2.5.2', 'pandas is built on top of it. We do not call it directly in this step, but NaN (missing value) comes from numpy.'],
    ['seaborn', '0.13.2', 'Installed in this step but not used yet. It draws the correlation heatmap (later step).'],
    ['matplotlib', '3.11.1', 'The drawing engine under seaborn. Used later for charts.'],
    ['scikit-learn', '1.9.0', 'Models, splits and metrics. Not used until the modelling stage.'],
    ['scipy', '1.18.0', 'Statistics helpers. Later.'],
]), [28*mm, 20*mm, 126*mm])

# ---------------------------------------------------------------- 1
P('1. Why do a "first look" at all?', H2)
P('A common beginner mistake is to jump straight '
  'to modelling. A model will happily train on garbage and give you a score. A score you cannot explain is worthless '
  'in an interview. So the very first job is only to <b>look</b> and <b>not change anything</b>.')
P('The first look answers four basic questions, each of which can stop us from wasting time later:')
B(['<b>Is it the right file, and is it complete?</b> (shape)',
   '<b>What kind of thing is each column?</b> number, text, date (dtypes)',
   '<b>What does an actual row look like?</b> (head) Real values show things summaries hide.',
   '<b>How balanced is the thing we want to predict?</b> (target counts) This decides which metrics are even valid.'])

# ---------------------------------------------------------------- 2
P('2. Environment check', H2)
P('Before loading data we confirmed three things about the setup:')
table(wrap([
    ['Item', 'Result', 'Meaning'],
    ['data/hotel_bookings.csv', 'Present, 16.9 MB', 'The dataset is in place. Small enough to load fully into memory on a laptop - this is what "medium-scale" means in practice.'],
    ['pandas, numpy, sklearn, matplotlib, scipy, jupyter', 'Installed', 'Everything needed for exploration and modelling was already available.'],
    ['seaborn', 'Was missing -> installed 0.13.2', 'Needed for the correlation heatmap. We asked you before installing because installing changes your environment.'],
    ['.gitignore', 'Contains "data/"', 'The raw data stays out of git. Good practice: data files are large, can change, and may have licence limits. Code goes in git, data does not.'],
]), [48*mm, 38*mm, 88*mm])

# ---------------------------------------------------------------- 3
P('3. The code we ran', H2)
P('Saved in this same folder as <b>STEP_1_first_look.py</b>. You can run it yourself from the project root: <font face="Courier">python data_exploration/STEP_1_First_Look/STEP_1_first_look.py</font>')
C('''import pandas as pd

pd.set_option('display.width', 200)        # wider printing so columns do not wrap
pd.set_option('display.max_columns', 50)   # show all columns instead of "..."

df = pd.read_csv('data/hotel_bookings.csv')   # load CSV into a DataFrame called df

print(df.shape)                 # (rows, columns)
print(df.dtypes)                # data type of every column
print(df.head(3).T)             # first 3 rows, transposed so columns run down the page
print(df['is_canceled'].value_counts())                 # counts of 0 and 1
print(df['is_canceled'].value_counts(normalize=True))   # same, as fractions''')
P('<b>Line-by-line reasoning:</b>')
B(['<b>pd.read_csv</b> reads the file into a DataFrame. A DataFrame is a table: each row is one booking, each column is one attribute.',
   '<b>df.shape</b> returns (number of rows, number of columns). It is the cheapest sanity check there is.',
   '<b>df.dtypes</b> lists how pandas interpreted each column. pandas guesses from the contents, and guesses can be wrong.',
   '<b>df.head(3).T</b> shows the first 3 rows. The .T (transpose) flips it so the 32 column names run down the left side - with 32 columns, '
   'a normal head() is too wide to read.',
   '<b>value_counts()</b> counts each distinct value. With normalize=True it gives fractions instead of counts.'])
NT('<b>A small mistake worth remembering:</b> my first attempt used the flag <font face="Courier">python -I</font> '
   '(isolated mode, a safety option that ignores user-installed packages). pandas lives in the user packages, so Python '
   'said "No module named pandas". Lesson: this error does not always mean "not installed" - it can mean "installed '
   'somewhere Python is not looking". Interview-worthy debugging habit: check <i>where</i> Python looks before reinstalling.')

# ---------------------------------------------------------------- 4
P('4. Result 1 - Shape', H2)
C('SHAPE: (119390, 32)')
P('119,390 rows and 32 columns. This matches the published paper (Antonio, Almeida and Nunes), so we have the correct, '
  'complete file. <b>Each row is one booking</b> (one reservation), not one guest and not one night. That distinction matters: '
  'the same guest can appear in several rows, and one row can cover many nights.')
P('<b>Why this matters:</b> if the shape were, say, 60,000 rows, we would suspect a broken download. Also, 119K rows is '
  'comfortable for classical ML (trees, boosting, logistic regression) and large enough that a few percent of weird rows '
  'will not break a model - but it is small enough that we can inspect problems by hand.')

# ---------------------------------------------------------------- 5
P('5. Result 2 - Column data types', H2)
P('Here are all 32 columns with the type pandas assigned, and what that type tells us:')
dt = [
 ['hotel','object (text)','City Hotel or Resort Hotel. Categorical.'],
 ['is_canceled','int64','TARGET. 0 = not cancelled, 1 = cancelled.'],
 ['lead_time','int64','Days between booking and arrival.'],
 ['arrival_date_year','int64','2015, 2016 or 2017.'],
 ['arrival_date_month','object','Month NAME as text (July...). Needs ordering/encoding later.'],
 ['arrival_date_week_number','int64','Week of the year.'],
 ['arrival_date_day_of_month','int64','Day number.'],
 ['stays_in_weekend_nights','int64','Weekend nights in the stay.'],
 ['stays_in_week_nights','int64','Weekday nights in the stay.'],
 ['adults / babies','int64','Guest counts.'],
 ['children','float64','Guest count, but float -> it has missing values (see below).'],
 ['meal','object','Meal plan code (BB, HB, FB, SC, Undefined).'],
 ['country','object','Country code (ISO-style, e.g. PRT = Portugal).'],
 ['market_segment / distribution_channel','object','How the booking came in (online agency, direct, corporate...).'],
 ['is_repeated_guest','int64','1 if the guest stayed before.'],
 ['previous_cancellations / previous_bookings_not_canceled','int64','Guest history counts.'],
 ['reserved_room_type / assigned_room_type','object','Room booked vs room actually given.'],
 ['booking_changes','int64','How many times the booking was modified.'],
 ['deposit_type','object','No Deposit / Non Refund / Refundable.'],
 ['agent','float64','Travel agent ID. Float -> has missing values.'],
 ['company','float64','Company ID. Float -> has missing values (mostly missing, as you knew).'],
 ['days_in_waiting_list','int64','Days before booking was confirmed.'],
 ['customer_type','object','Transient, Contract, Group, Transient-party.'],
 ['adr','float64','Average Daily Rate. Regression target. Continuous number.'],
 ['required_car_parking_spaces / total_of_special_requests','int64','Counts.'],
 ['reservation_status','object','Check-Out / Canceled / No-Show. LEAKS the target.'],
 ['reservation_status_date','object','Date stored as TEXT. Also leaks the target.'],
]
table(wrap([['Column', 'pandas type', 'What it means / what the type tells us']] + dt), [56*mm, 26*mm, 92*mm])

P('Three dtype lessons', H3)
B(['<b>object means text.</b> Models cannot use text directly, so every object column will need encoding (turning categories into numbers). '
   'How we encode depends on the column - that will be a separate documented decision.',
   '<b>Float where you expect whole numbers is a clue.</b> children, agent and company are float64 although they are counts or IDs. '
   'pandas stores missing values as NaN, and NaN only exists in float columns, so one missing value forces the whole column to float. '
   'In the rows we saw, agent and company show NaN directly.',
   '<b>Dates stored as text.</b> reservation_status_date is object. If we ever used it, we would convert it with pd.to_datetime first. '
   '(We will most likely drop it because of leakage - see section 7.)'])

# ---------------------------------------------------------------- 6
P('6. Result 3 - The first rows (what real data looks like)', H2)
P('We printed the first 3 rows transposed. All three are Resort Hotel bookings for 1 July 2015 and all three were not cancelled. '
  'Key values:')
table(wrap([
    ['Column', 'Row 0', 'Row 1', 'Row 2'],
    ['lead_time', '342', '737', '7'],
    ['adults', '2', '2', '1'],
    ['stays (weekend / week nights)', '0 / 0', '0 / 0', '0 / 1'],
    ['reserved_room_type', 'C', 'C', 'A'],
    ['assigned_room_type', 'C', 'C', 'C'],
    ['booking_changes', '3', '4', '0'],
    ['agent / company', 'NaN / NaN', 'NaN / NaN', 'NaN / NaN'],
    ['adr', '0.0', '0.0', '75.0'],
    ['reservation_status', 'Check-Out', 'Check-Out', 'Check-Out'],
    ['reservation_status_date', '2015-07-01', '2015-07-01', '2015-07-02'],
]), [60*mm, 38*mm, 38*mm, 38*mm])

P('Things we noticed (each one is a question to investigate later, not a conclusion yet)', H3)
B(['<b>lead_time = 737 (row 1).</b> About two years between booking and arrival. This fits your hypothesis (long lead time means '
   'higher cancellation risk) but it is also an extreme value. Is it a genuine early booking or a data oddity? We will check the '
   'distribution of lead_time and see how common values this large are.',
   '<b>adr = 0.0 for rows 0 and 1</b>, even though the guests checked out. A price of zero for a real stay is strange. Possible explanations: '
   'complimentary stay, internal/staff booking, a special booking type, or missing data recorded as 0. We must not guess - we will '
   'look at which rows have adr = 0 and what else is true of them.',
   '<b>Rows 0 and 1 have 0 stay nights</b> (0 weekend + 0 week nights). A stay of zero nights is another oddity (same-day or data entry). '
   'Worth counting later.',
   '<b>reserved_room_type = A but assigned_room_type = C (row 2).</b> The room the guest got differs from the room booked. The assigned room '
   'is decided at or near check-in, so it may not be known when a prediction is needed. This is a <b>leakage candidate</b>.',
   '<b>reservation_status = Check-Out on all three rows, all with is_canceled = 0.</b> The status states the outcome. See section 7.',
   '<b>agent and company are NaN on all three rows.</b> Consistent with the "mostly missing" issue you already knew about.'])

# ---------------------------------------------------------------- 7
P('7. Result 4 - The target and class imbalance', H2)
C('''is_canceled
0    75166
1    44224

is_canceled
0    0.6296
1    0.3704''')
table(wrap([
    ['Class', 'Meaning', 'Count', 'Share'],
    ['0', 'Not cancelled', '75,166', '62.96%'],
    ['1', 'Cancelled', '44,224', '37.04%'],
    ['Total', '', '119,390', '100%'],
]), [24*mm, 50*mm, 40*mm, 40*mm])
P('<b>Is 37% imbalanced?</b> Yes, moderately. It is not extreme like fraud detection (often under 1%), but the classes are clearly unequal. '
  'The more important effect is on <b>metrics</b>.')

P('The "always say no" baseline', H3)
P('Imagine a useless model that predicts "not cancelled" for every single booking. Its accuracy would be:')
C('''accuracy = correct predictions / all predictions
         = 75,166 / 119,390
         = 0.6296  ->  62.96%''')
P('It scores almost 63% while catching <b>zero</b> of the 44,224 cancellations - and catching cancellations is the only reason the model exists. '
  'This is called the <b>majority-class baseline</b> (or "dummy classifier"). It gives us a floor: any real model must clearly beat '
  '62.96% accuracy, and accuracy alone cannot even show whether it does so in a useful way.')
NT('<b>This is the start of your answer to the question "why ROC-AUC and not accuracy?"</b> Accuracy rewards getting the big class '
   'right and can look good while the model is useless on the class you care about. The full justification (with formulas for recall, precision, '
   'F1, TPR, FPR, ROC and AUC) gets its own dedicated PDF in the metrics stage.')

P('Why leakage is already visible', H3)
P('<b>Data leakage</b> means a feature contains information that would not be available at the moment we need to make the prediction, '
  'or that directly encodes the answer. The model then looks brilliant in testing and fails in the real world.')
B(['<b>reservation_status</b> takes the values Check-Out, Canceled, No-Show. It is literally the outcome written in words. '
   'Using it to predict is_canceled is like predicting an exam result from the already-printed marksheet.',
   '<b>reservation_status_date</b> is the date that status was set, so it also depends on the outcome.',
   '<b>Test to apply to every column:</b> "At the moment a booking is made (or whenever we run the prediction), would I truly know this value?" '
   'If no, it cannot be a feature. Next step we will apply this test to all 32 columns.'])

# ---------------------------------------------------------------- 8
P('8. Summary: what we learned in Step 1', H2)
table(wrap([
    ['Check', 'Finding', 'Consequence'],
    ['Shape', '119,390 x 32', 'Correct file; one row = one booking.'],
    ['Types', '12 text-type columns, 3 float columns with gaps, rest integers', 'Encoding needed for text; float columns hide missing values.'],
    ['Target', '62.96% / 37.04%', 'Moderately imbalanced; accuracy is misleading; baseline to beat = 62.96%.'],
    ['Leakage', 'reservation_status and its date clearly leak', 'Must be excluded from features. assigned_room_type is a suspect.'],
    ['Oddities', 'lead_time 737, adr 0, zero-night stays, NaN agent/company', 'Each needs a documented investigation, not a blind fix.'],
]), [28*mm, 70*mm, 76*mm])

# ---------------------------------------------------------------- 9
P('9. Interview questions from this step (with model answers)', H2)
qa = [
 ('Your target is 37% positive. Is that imbalanced? How do you detect it and what can you do?',
  'Detect it with value_counts(normalize=True). 37/63 is moderately imbalanced. Options: choose metrics that do not depend on class ratio '
  '(recall, precision, F1, ROC-AUC, PR-AUC), use stratified train/test splits so both sets keep the 37/63 ratio, use class weights, or resample '
  '(oversample minority / undersample majority). With 37% we usually start with proper metrics and stratification before touching resampling.'),
 ('A model gets 63% accuracy on this data. Is it good?',
  'Not necessarily. 62.96% is exactly what a model gets by always predicting "not cancelled". Accuracy of 63% could mean the model learned nothing. '
  'We compare against this baseline and look at recall/precision on the cancelled class.'),
 ('Why did pandas make children, agent and company float64?',
  'These columns contain missing values stored as NaN. NaN is a floating-point concept, so a column of integers with even one NaN becomes float. '
  'It is a hint to check for missing data. (Newer pandas "nullable" integer type Int64 can hold missing values without becoming float.)'),
 ('What is data leakage? Give an example from your project.',
  'Leakage is when a feature carries information not available at prediction time or encodes the target. Here, reservation_status contains '
  '"Canceled" or "No-Show" for exactly the rows where is_canceled = 1 (confirmed with a cross-table in Step 2), so a model using it would score near perfect and be useless in production, '
  'because at booking time the status does not exist yet.'),
 ('A price column has 0 for some rows. What do you do?',
  'Investigate before acting. Count them, look at other columns for those rows (nights, segment, status), and decide: genuine free stay (keep, '
  'maybe flag), error/missing-coded-as-zero (impute or drop), or outlier. Document the decision and the reason. Never silently delete.'),
 ('Why look at the data before modelling?',
  'Models cannot tell sense from nonsense: they will train on duplicated rows, leaked columns, impossible values and still output a score. '
  'Only inspection reveals these problems, and a score built on them cannot be defended.'),
 ('What does one row represent in this dataset and why does it matter?',
  'One booking. It matters because the same guest or same hotel stay-period can appear several times, so rows are not fully independent - '
  'relevant when we split data for validation and when we interpret counts.'),
]
for i, (q, a) in enumerate(qa, 1):
    story.append(KeepTogether([Paragraph(f'<b>Q{i}. {q}</b>', BODY), Paragraph(f'<i>Answer:</i> {a}', BODY), Spacer(1, 4)]))

# ---------------------------------------------------------------- 10
P('10. Self-check (answer these in your own words before Step 2)', H2)
B(['Why did we only look and not clean in this step?',
   'What accuracy does a "never cancelled" model get here, and why does that make accuracy a poor sole metric?',
   'Why are children, agent and company floats?',
   'Name two columns that leak the target and explain the test you used to decide.',
   'What would worry you about a row with lead_time = 737 and adr = 0?'])

P('What comes next: STEP 2 - Data Dictionary', H2)
P('We go through all 32 columns one by one: meaning, type, missing count, number of unique values, and a clear verdict - '
  '<b>usable feature, needs care, or leakage</b> - with the reason written down.')

def footer(c, d):
    c.saveState(); c.setFont('Helvetica', 8); c.setFillColor(colors.grey)
    c.drawString(18*mm, 10*mm, 'Hotel Booking Cancellation ML | STEP 1 - First Look at the Data')
    c.drawRightString(A4[0]-18*mm, 10*mm, f'Page {d.page}')
    c.restoreState()

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=18*mm,
                        title='STEP 1 - First Look at the Data', author='Mitansh Kanani')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('written', out)
