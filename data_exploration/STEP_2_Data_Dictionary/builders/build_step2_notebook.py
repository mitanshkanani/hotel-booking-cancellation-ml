"""Builds data_exploration/STEP_2_data_dictionary.ipynb and executes it."""
import sys
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
folder = HERE.parent                                   # STEP_2_Data_Dictionary/ (notebook runs here)
extra_cells = (HERE / 'step2_extra_cells.py').read_text(encoding='utf-8')

nb = nbf.v4.new_notebook()
cells = []
def md(t): cells.append(nbf.v4.new_markdown_cell(t))
def code(t): cells.append(nbf.v4.new_code_cell(t))

md("""# STEP 2 - Data Dictionary and Leakage Audit

**Goal:** understand every one of the 32 columns: its type, how many values are missing, how many distinct values it has,
and - most important - whether it is **safe to use as a feature**.

**Why now:** Step 1 only looked at the data. Before any cleaning or modelling we need a per-column fact sheet,
and we need to test the leakage suspects with evidence instead of opinion.

**Libraries:** pandas (tables), numpy (numbers/NaN), matplotlib (charts, saved as SVG only).""")

code("""from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)

DATA = Path('..') / '..' / 'data' / 'hotel_bookings.csv'
FIG = Path('figures')          # every chart in this project is saved as SVG only
FIG.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
print(df.shape)""")

md("""## Part A - Column profile (the raw facts)

For every column: data type, count of missing values, % missing, number of distinct values, and one example.
**Why:** missing counts tell us where cleaning is needed; distinct counts separate IDs/categories (few values)
from continuous numbers (many values) and warn about high-cardinality columns that are hard to encode.""")

code("""profile = pd.DataFrame({
    'dtype': df.dtypes.astype(str),
    'missing': df.isna().sum(),
    'missing_pct': (df.isna().mean() * 100).round(2),
    'n_unique': df.nunique(),
    'example': df.apply(lambda s: s.dropna().iloc[0]),
})
profile""")

md("""## Part B - Missing values chart

**Why a chart:** a number like 94.3% is easy to forget; a bar chart shows at a glance which columns are a real problem.""")

code("""miss = profile.loc[profile['missing'] > 0, 'missing_pct'].sort_values()
print(miss)

fig, ax = plt.subplots(figsize=(7, 3))
bars = ax.barh(miss.index, miss.values, color='#2F6DB5')
ax.set_xlabel('% of rows missing')
ax.set_title('Missing values per column (only columns with gaps)')
ax.set_xlim(0, 105)
for b, v in zip(bars, miss.values):
    ax.text(v + 1, b.get_y() + b.get_height() / 2, f'{v:.2f}%', va='center', fontsize=9)
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(FIG / 'step2_missing_values.svg')
plt.show()""")

md("""## Part C - Hidden missing values and category codes

pandas only counts true blanks as missing. Text such as `Undefined` is a **disguised missing value**: present in the file,
but it means "unknown". We list every value of each low-cardinality text column to find them and to verify what the codes really are.""")

code("""text_cols = [c for c in df.select_dtypes('object').columns if c not in ('reservation_status_date',)]
for c in text_cols:
    vc = df[c].value_counts(dropna=False)
    print(f'--- {c}  ({df[c].nunique()} distinct) ---')
    print(vc.head(12).to_string())
    print()""")

md("""## Part D - Numeric summary

`describe()` gives min, max, mean and quartiles. **Why:** impossible values (negative counts, absurd maximums) and
suspicious zeros show up in min and max long before any chart does.""")

code("""num_cols = df.select_dtypes('number').columns
df[num_cols].describe().T.round(2)""")

md("""## Part E - Leakage audit

**Leakage test:** *"At the moment a booking is made, would I really know this value?"* If not, it cannot be a feature.
We test each suspect with data, not opinion.

### E1. reservation_status vs is_canceled""")

code("""pd.crosstab(df['reservation_status'], df['is_canceled'], margins=True)""")

md("""### E2. reservation_status_date - is it an after-the-fact date?

We rebuild the departure date (arrival date + nights stayed). If for Check-Out rows the status date equals the departure date,
the column is recorded *after the stay*, so it cannot be known when the booking is made.""")

code("""arrival = pd.to_datetime(
    df['arrival_date_year'].astype(str) + '-' + df['arrival_date_month'] + '-' + df['arrival_date_day_of_month'].astype(str),
    format='%Y-%B-%d')
nights = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
departure = arrival + pd.to_timedelta(nights, unit='D')
status_date = pd.to_datetime(df['reservation_status_date'])

co = df['reservation_status'] == 'Check-Out'
print('Check-Out rows where status date == departure date: '
      f'{(status_date[co] == departure[co]).mean():.4f}')

ca = df['reservation_status'] == 'Canceled'
days_before = (arrival[ca] - status_date[ca]).dt.days
print('Canceled rows: status date is BEFORE arrival for', f'{(days_before > 0).mean():.4f}', 'of rows')
print('Median days between cancellation date and arrival:', days_before.median())""")

md("""### E2b. How much does this date alone give away?

Define `gap = reservation_status_date - arrival_date` (in days). A cancellation happens BEFORE or ON the arrival date (gap <= 0).
A completed stay ends AFTER arrival (gap > 0). So one simple rule - *"gap <= 0 means cancelled"* - needs no model at all.""")

code("""gap = (status_date - arrival).dt.days
rule_pred = (gap <= 0).astype(int)          # the whole 'model': cancelled if the date is on/before arrival
print('Accuracy of the one-line rule  gap <= 0  ->  cancelled:', round((rule_pred == df['is_canceled']).mean(), 4))
print('Baseline (always predict not cancelled)                :', round((df['is_canceled'] == 0).mean(), 4))
print()
print(pd.crosstab(rule_pred.rename('rule says cancelled'), df['is_canceled'], margins=True))""")

md("""### E3. Suspects: assigned_room_type, booking_changes, days_in_waiting_list

For each suspect we compare the **cancellation rate** across groups. A huge gap is a *signal* - but a signal is not the same as leakage.
Leakage depends on **timing**: was the value known when the prediction is needed?""")

code("""df['room_changed'] = (df['reserved_room_type'] != df['assigned_room_type']).astype(int)

def rate(by, name=None):
    t = df.groupby(by)['is_canceled'].agg(rows='size', cancel_rate='mean').round(4)
    t.index.name = name or (by if isinstance(by, str) else None)
    return t

print('room_changed (reserved != assigned)'); print(rate('room_changed')); print()
print('booking_changes (capped at 3+)'); print(rate(df['booking_changes'].clip(upper=3), 'booking_changes')); print()
print('days_in_waiting_list > 0'); print(rate(df['days_in_waiting_list'].gt(0).astype(int), 'waiting>0')); print()
print('deposit_type'); print(rate('deposit_type'))""")

if extra_cells:
    exec(extra_cells)  # appends more md()/code() calls

nb['cells'] = cells
client = NotebookClient(nb, timeout=900, kernel_name='python3', resources={'metadata': {'path': str(folder)}})
client.execute()
out = folder / 'STEP_2_data_dictionary.ipynb'
nbf.write(nb, out)
print('written', out)
