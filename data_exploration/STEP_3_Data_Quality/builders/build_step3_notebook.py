"""Builds data_exploration/STEP_3_Data_Quality/STEP_3_data_quality.ipynb and executes it.

Run from anywhere:  python data_exploration/STEP_3_Data_Quality/builders/build_step3_notebook.py
The decision cells live in step3_extra_cells.py (appended after the evidence cells).
"""
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
folder = HERE.parent                                  # STEP_3_Data_Quality/ (notebook runs here)
extra_cells = (HERE / 'step3_extra_cells.py').read_text(encoding='utf-8')

nb = nbf.v4.new_notebook()
cells = []
def md(t): cells.append(nbf.v4.new_markdown_cell(t))
def code(t): cells.append(nbf.v4.new_code_cell(t))

md("""# STEP 3 - Data Quality

**Goal:** investigate every oddity noticed in Steps 1 and 2 and decide, with evidence, what to do with each:
**drop, fix, flag (keep but mark), or keep.**

**Why before EDA and modelling:** correlations, averages and models are all distorted by impossible or duplicated rows. We must know what is broken first.

**Rule of this step:** *investigate before acting.* A weird value is not automatically an error (a free stay can have adr = 0).
We ask: is it an error, a rare-but-real case, or an outlier, and what does it do to the thing we predict?

**Libraries:** pandas, numpy, matplotlib (charts saved as SVG only).""")

code("""from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)

DATA = Path('..') / '..' / 'data' / 'hotel_bookings.csv'
FIG = Path('figures')          # SVG only
FIG.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
ORIG = list(df.columns)        # the 32 original columns
LEAK = ['reservation_status', 'reservation_status_date', 'assigned_room_type', 'required_car_parking_spaces']  # Step 2

# helper columns (derived, not in the file)
df['total_guests'] = df['adults'] + df['children'].fillna(0) + df['babies']
df['total_nights'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']

def summ(mask, label):
    sub = df[mask]
    return pd.Series({'rows': len(sub), 'pct_of_data': round(len(sub) / len(df) * 100, 2),
                      'cancel_rate': round(sub['is_canceled'].mean(), 4) if len(sub) else np.nan,
                      'mean_adr': round(sub['adr'].mean(), 2) if len(sub) else np.nan}, name=label)

print(df.shape, '| overall cancel rate', round(df['is_canceled'].mean(), 4))""")

# ------------------------------------------------------------------ A
md("""## Part A - Duplicate rows

A **duplicate** is a row identical to an earlier row in all 32 columns. Two reasons to care:
1. Duplicates give some bookings extra weight in training.
2. **Leakage across the split:** if one copy lands in the training set and another in the test set, the model is tested on a row it has already seen, so the test score is inflated.

But identical rows are not always errors: two people can genuinely book the same thing (e.g. a group booking several identical rooms). So we check the evidence.""")

code("""n_dup = df[ORIG].duplicated().sum()
print(f'Rows that are a 2nd+ copy of an earlier row: {n_dup:,} ({n_dup / len(df):.2%})')

dup_any = df[ORIG].duplicated(keep=False)
print(f'Rows belonging to any duplicate group (all copies): {dup_any.sum():,}')
print('cancel rate - rows in duplicate groups:', round(df.loc[dup_any, 'is_canceled'].mean(), 4),
      '| unique rows:', round(df.loc[~dup_any, 'is_canceled'].mean(), 4))

sizes = df[dup_any].groupby(ORIG, dropna=False).size()
print('\\nnumber of distinct duplicate groups:', len(sizes))
print('copies per group (value counts of group size):')
print(sizes.value_counts().sort_index().head(8).to_string())

print('\\nshare of rows in a duplicate group, by market_segment:')
print(df.assign(dup=dup_any).groupby('market_segment')['dup'].mean().round(3).sort_values(ascending=False).to_string())""")

md("""### A2. Do identical *features* ever have different outcomes?

Modelling will not use the 4 leakage columns. After removing them, bookings can look identical to the model yet have different `is_canceled`.
Such **conflicting groups** are label noise: the model cannot be right for all of them.""")

code("""FEATS = [c for c in ORIG if c not in LEAK + ['is_canceled']]
g = df.groupby(FEATS, dropna=False)['is_canceled'].agg(size='size', n_labels='nunique')
print('groups of feature-identical bookings:', f'{len(g):,}')
print('groups with more than one booking   :', f'{(g["size"] > 1).sum():,}')
print('groups with BOTH outcomes (conflict) :', f'{(g["n_labels"] > 1).sum():,}')
print('rows inside conflicting groups       :', f'{g.loc[g["n_labels"] > 1, "size"].sum():,}')

# how many rows are exact copies once the leakage columns are ignored
n_dup_feat = df[FEATS + ['is_canceled']].duplicated().sum()
print('\\n2nd+ copies when leakage columns are ignored (features + target):', f'{n_dup_feat:,}', f'({n_dup_feat / len(df):.2%})')""")

# ------------------------------------------------------------------ B
md("""## Part B - Zero-guest bookings

`total_guests = adults + children + babies`. A booking with zero guests cannot be a real stay by a person. We check how many exist and what they look like.""")

code("""zg = df['total_guests'] == 0
print(summ(zg, 'zero guests').to_string())
print('\\nzero-adult rows (any children/babies):', (df['adults'] == 0).sum(),
      '| zero-adult but children or babies present:', ((df['adults'] == 0) & (df['total_guests'] > 0)).sum())
print('\\nhotel:');            print(df.loc[zg, 'hotel'].value_counts().to_string())
print('\\nmarket_segment:');   print(df.loc[zg, 'market_segment'].value_counts().to_string())
print('\\nreservation_status:'); print(df.loc[zg, 'reservation_status'].value_counts().to_string())
print('\\nadr of zero-guest rows:'); print(df.loc[zg, 'adr'].describe().round(2).to_string())
print('\\ntotal_nights of zero-guest rows:'); print(df.loc[zg, 'total_nights'].describe().round(2).to_string())""")

# ------------------------------------------------------------------ C
md("""## Part C - Zero-night stays

`total_nights = stays_in_weekend_nights + stays_in_week_nights`. A stay of 0 nights is either a same-day use, an error, or a booking that never became a stay.""")

code("""zn = df['total_nights'] == 0
print(summ(zn, 'zero nights').to_string())
print('\\nreservation_status:'); print(df.loc[zn, 'reservation_status'].value_counts().to_string())
print('\\nmarket_segment:');   print(df.loc[zn, 'market_segment'].value_counts().to_string())
print('\\nhotel:');            print(df.loc[zn, 'hotel'].value_counts().to_string())
print('\\nadr of zero-night rows:'); print(df.loc[zn, 'adr'].describe().round(2).to_string())
print('\\noverlap: zero nights AND zero guests:', (zn & zg).sum())
print('overlap: zero nights AND adr == 0     :', (zn & (df['adr'] == 0)).sum())""")

# ------------------------------------------------------------------ D
md("""## Part D - adr problems (negative, zero, extreme)

`adr` = average daily rate (price per night). It is the regression target and also a possible feature, so bad values matter twice.""")

code("""neg = df['adr'] < 0
print('negative adr rows:', neg.sum())
print(df.loc[neg, ['hotel', 'arrival_date_year', 'arrival_date_month', 'market_segment', 'reserved_room_type', 'total_nights', 'adr', 'reservation_status']].T.to_string())""")

code("""zero = df['adr'] == 0
print(summ(zero, 'adr == 0').to_string())
print('\\nreservation_status of adr == 0 rows:'); print(df.loc[zero, 'reservation_status'].value_counts().to_string())
print('\\nmarket_segment of adr == 0 rows (count) and share of each segment that has adr == 0:')
t = pd.DataFrame({'adr0_rows': df.loc[zero, 'market_segment'].value_counts(),
                  'segment_rows': df['market_segment'].value_counts()}).fillna(0).astype(int)
t['share_adr0_in_segment'] = (t['adr0_rows'] / t['segment_rows']).round(3)
print(t.sort_values('adr0_rows', ascending=False).to_string())
print('\\nadr == 0 and total_nights == 0:', (zero & zn).sum(), '| adr == 0 and total_nights > 0:', (zero & ~zn).sum())""")

code("""print('adr quantiles:'); print(df['adr'].quantile([0.5, 0.9, 0.99, 0.999, 0.9999, 1.0]).round(2).to_string())
print('\\ntop 6 adr rows:')
print(df.nlargest(6, 'adr')[['hotel', 'arrival_date_year', 'arrival_date_month', 'market_segment', 'reserved_room_type',
                             'adults', 'total_nights', 'adr', 'is_canceled']].to_string())
print('\\nadr by hotel (median, 99th percentile, max):')
print(df.groupby('hotel')['adr'].agg(median='median', p99=lambda s: s.quantile(0.99), max='max').round(2).to_string())
print('\\nrows with adr > 300:', (df['adr'] > 300).sum(), '| adr > 500:', (df['adr'] > 500).sum(), '| adr > 1000:', (df['adr'] > 1000).sum())""")

code("""x = df['adr'].clip(upper=df['adr'].quantile(0.995))   # clip only for display so the extreme row does not squash the chart
fig, ax = plt.subplots(figsize=(7.5, 3.6))
ax.hist(x, bins=60, color='#2F6DB5')
ax.axvline(df['adr'].median(), color='black', linestyle='--', linewidth=1)
ax.text(df['adr'].median() + 3, ax.get_ylim()[1] * 0.92, f'median {df["adr"].median():.0f}', fontsize=8)
ax.set_xlabel('adr (price per night), clipped at the 99.5th percentile for display')
ax.set_ylabel('number of bookings')
ax.set_title(f'adr distribution (true max = {df["adr"].max():.0f}, true min = {df["adr"].min():.2f})')
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(FIG / 'step3_adr_distribution.svg')
plt.show()""")

# ------------------------------------------------------------------ E
md("""## Part E - Other extreme values

For each numeric column we look at the median, the 99th percentile, the 99.9th percentile and the maximum.
If the maximum is far above the 99.9th percentile, a handful of rows are extreme. Then we count rows above sensible thresholds.""")

code("""cols = ['lead_time', 'adults', 'children', 'babies', 'total_nights', 'days_in_waiting_list',
        'previous_cancellations', 'previous_bookings_not_canceled', 'booking_changes']
q = df[cols].quantile([0.5, 0.99, 0.999, 1.0]).T
q.columns = ['median', 'p99', 'p99.9', 'max']
print(q.round(2).to_string())

print('\\nrows above sensible thresholds:')
thr = {'adults >= 5': df['adults'] >= 5, 'children >= 4': df['children'] >= 4, 'babies >= 3': df['babies'] >= 3,
       'total_nights >= 15': df['total_nights'] >= 15, 'lead_time >= 500': df['lead_time'] >= 500,
       'days_in_waiting_list >= 200': df['days_in_waiting_list'] >= 200}
print(pd.DataFrame([summ(m, k) for k, m in thr.items()]).to_string())""")

if extra_cells.strip():
    exec(extra_cells)  # appends decision cells with md()/code()

nb['cells'] = cells
client = NotebookClient(nb, timeout=900, kernel_name='python3', resources={'metadata': {'path': str(folder)}})
client.execute()
out = folder / 'STEP_3_data_quality.ipynb'
nbf.write(nb, out)
print('written', out)
