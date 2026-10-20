md("""### E4. The evidence as a chart

Dashed line = overall cancellation rate (37.04%). Bars far from the line mean the group behaves very differently - a strong signal.
Whether that signal is *legitimate* or *leakage* is decided by timing, which is why we need the verdict in Part F.""")

code("""groups = {
    'room not changed': df.loc[df['room_changed'] == 0, 'is_canceled'].mean(),
    'room changed': df.loc[df['room_changed'] == 1, 'is_canceled'].mean(),
    '0 booking changes': df.loc[df['booking_changes'] == 0, 'is_canceled'].mean(),
    '1+ booking changes': df.loc[df['booking_changes'] >= 1, 'is_canceled'].mean(),
    'no waiting list': df.loc[df['days_in_waiting_list'] == 0, 'is_canceled'].mean(),
    'was on waiting list': df.loc[df['days_in_waiting_list'] > 0, 'is_canceled'].mean(),
    'deposit: No Deposit': df.loc[df['deposit_type'] == 'No Deposit', 'is_canceled'].mean(),
    'deposit: Non Refund': df.loc[df['deposit_type'] == 'Non Refund', 'is_canceled'].mean(),
}
overall = df['is_canceled'].mean()
colors = ['#2F6DB5', '#D9822B'] * 4

fig, ax = plt.subplots(figsize=(7.5, 3.8))
y = np.arange(len(groups))[::-1]
ax.barh(y, [v * 100 for v in groups.values()], color=colors)
ax.set_yticks(y)
ax.set_yticklabels(list(groups.keys()))
ax.axvline(overall * 100, color='black', linestyle='--', linewidth=1)
ax.text(overall * 100 + 1, y.max() + 0.55, f'overall {overall:.1%}', fontsize=8)
for yi, v in zip(y, groups.values()):
    ax.text(v * 100 + 1, yi, f'{v:.1%}', va='center', fontsize=9)
ax.set_xlim(0, 112)
ax.set_xlabel('cancellation rate (%)')
ax.set_title('Cancellation rate for the leakage suspects')
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(FIG / 'step2_suspect_cancel_rates.svg')
plt.show()""")

md("""## Part F - Leakage re-audit of ALL columns

So far we tested suspects one by one, by logic. A careful audit also uses a second, data-driven check, so we do not miss a column.

**The idea (single-feature screen):** for each column, train a tiny decision tree (depth 5) that sees ONLY that one column, and measure how well it predicts
`is_canceled` using cross-validated **ROC-AUC** (5 folds). AUC is 0.5 for random guessing and 1.0 for perfect prediction.
A column that alone gets a near-perfect AUC is almost certainly leaking the answer.

**Limit of this screen:** it detects *how strong* a column is, not *when* it becomes known. A strong but legitimate column (like lead_time) also scores high.
So the screen tells us where to look; the timing logic decides. We use both.""")

code("""from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

feature_cols = [c for c in df.columns if c not in ('is_canceled', 'room_changed')]
y = df['is_canceled']
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

scores = {}
for c in feature_cols:
    s = df[c]
    if s.dtype == 'object':
        x = pd.factorize(s, sort=True)[0]          # text -> integer codes (sorted, so ISO dates keep their order)
    else:
        x = s.fillna(-1).to_numpy()                # NaN -> -1 so the tree can still use the column
    tree = DecisionTreeClassifier(max_depth=5, random_state=42)
    scores[c] = cross_val_score(tree, np.asarray(x).reshape(-1, 1), y, cv=cv, scoring='roc_auc').mean()

screen = pd.Series(scores).sort_values(ascending=False).round(4)
print(screen.to_string())""")

code("""s_plot = screen.sort_values()
bar_colors = ['#C0392B' if v >= 0.9 else ('#D9822B' if v >= 0.7 else '#2F6DB5') for v in s_plot.values]

fig, ax = plt.subplots(figsize=(7.5, 7.2))
ax.barh(s_plot.index, s_plot.values, color=bar_colors)
ax.axvline(0.5, color='black', linestyle='--', linewidth=1)
ax.text(0.505, -0.9, 'random guessing = 0.5', fontsize=8)
for yi, v in enumerate(s_plot.values):
    ax.text(v + 0.005, yi, f'{v:.3f}', va='center', fontsize=7.5)
ax.set_xlim(0.45, 1.04)
ax.set_xlabel('cross-validated ROC-AUC using ONLY this column (depth-5 tree)')
ax.set_title('Single-column predictive power (red >= 0.9, orange >= 0.7)')
ax.tick_params(axis='y', labelsize=8)
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(FIG / 'step2_single_feature_auc.svg')
plt.show()""")

md("""### F1b. The screen's blind spot: leakage hidden in a RELATIONSHIP between two columns

`reservation_status_date` scored only about 0.64 on its own, yet we proved it is a near-perfect leak. The leak appears only when we combine
columns: `gap = status_date - arrival_date`. We also test `room_changed = (reserved_room_type != assigned_room_type)`.
Same screen, on these two derived columns. Expect `gap` to jump, while `room_changed` stays modest because it only applies to the ~12.5% of bookings whose room changed
(its leakage is decided by timing and mechanism, not by overall strength).""")

code("""pair_features = {'gap (status_date - arrival_date)': gap, 'room_changed': df['room_changed']}
for name, x in pair_features.items():
    auc = cross_val_score(DecisionTreeClassifier(max_depth=5, random_state=42),
                          x.fillna(-1).to_numpy().reshape(-1, 1), y, cv=cv, scoring='roc_auc').mean()
    print(f'{name:40s} AUC = {auc:.4f}')""")

md("""### F2. Checking the columns we have not yet looked at: parking, special requests, guest history, adr

These are the remaining columns whose timing is unclear. We look at the cancellation rate inside each group.""")

code("""print('required_car_parking_spaces'); print(rate(df['required_car_parking_spaces'].clip(upper=2), 'parking spaces (2 = 2+)')); print()
print('total_of_special_requests'); print(rate(df['total_of_special_requests'].clip(upper=3), 'special requests (3 = 3+)')); print()
print('previous_cancellations > 0'); print(rate(df['previous_cancellations'].gt(0).astype(int), 'prev cancellations>0')); print()
print('is_repeated_guest'); print(rate('is_repeated_guest')); print()
print('adr == 0 (share of rows) by outcome:')
print(df.assign(adr_zero=df['adr'].eq(0)).groupby('is_canceled')['adr_zero'].mean().round(4).to_string()); print()
print('mean adr by outcome:'); print(df.groupby('is_canceled')['adr'].mean().round(2).to_string())""")

md("""## Part G - The data dictionary with a verdict for every column

Verdict labels:
- **USABLE** - known at booking time, no problem seen yet.
- **NEEDS CARE** - usable only after a decision (missing values, outliers, odd values, or timing that must be checked).
- **LEAKAGE** - contains the answer or is only known after the outcome. Excluded from features.
- **TARGET** - a column we predict (`is_canceled` for classification, `adr` for regression).

These verdicts are our current judgment from the evidence above. Ablation experiments later will test the "NEEDS CARE" ones with scores.""")

code("""verdict = {
    'hotel': ('USABLE', 'Chosen at booking. Two values.'),
    'is_canceled': ('TARGET', 'Classification target. 1 includes both Canceled (43,017) and No-Show (1,207).'),
    'lead_time': ('USABLE', 'Known at booking. Skewed, max 737 days; check outliers in EDA.'),
    'arrival_date_year': ('NEEDS CARE', 'Only 2015-2017. A model cannot generalise to a year it never saw; decide how to split by time.'),
    'arrival_date_month': ('USABLE', 'Known at booking. Text month names need ordering/encoding.'),
    'arrival_date_week_number': ('NEEDS CARE', 'Overlaps with month: redundant information, check correlation.'),
    'arrival_date_day_of_month': ('USABLE', 'Known at booking, probably weak alone.'),
    'stays_in_weekend_nights': ('NEEDS CARE', 'Planned stay known at booking, but max 19 and zero-night stays exist (Step 3).'),
    'stays_in_week_nights': ('NEEDS CARE', 'Planned stay known at booking, but max 50 and zero-night stays exist (Step 3).'),
    'adults': ('NEEDS CARE', 'Known at booking, but zero-adult rows and max 55 exist (Step 3).'),
    'children': ('NEEDS CARE', '4 missing values (stored as NaN, hence float).'),
    'babies': ('USABLE', 'Known at booking. Max 10 looks odd; check in Step 3.'),
    'meal': ('NEEDS CARE', "'Undefined' (1,169 rows) is a disguised missing value."),
    'country': ('NEEDS CARE', '488 missing; 177 distinct values (high cardinality); PRT is about 41% of rows.'),
    'market_segment': ('NEEDS CARE', "'Undefined' appears in 2 rows; overlaps with distribution_channel."),
    'distribution_channel': ('NEEDS CARE', "'Undefined' appears in 5 rows; overlaps with market_segment."),
    'is_repeated_guest': ('USABLE', 'Guest history, known at booking.'),
    'previous_cancellations': ('USABLE', 'Guest history, known at booking. Heavily skewed; any previous cancellation -> 91.6% cancel (strong but legitimate).'),
    'previous_bookings_not_canceled': ('USABLE', 'Guest history, known at booking. Heavily skewed.'),
    'reserved_room_type': ('USABLE', 'Chosen at booking time.'),
    'assigned_room_type': ('LEAKAGE', 'Assigned at check-in. Room changed -> 5.4% cancel vs 41.6%: a room can only be reassigned for guests who arrive.'),
    'booking_changes': ('NEEDS CARE', 'LEAKAGE SUSPECT: final count includes changes made after booking (always 0 at booking time). Test by ablation.'),
    'deposit_type': ('NEEDS CARE', 'Non Refund shows 99.36% cancellation: opposite of common sense. Investigate before trusting.'),
    'agent': ('NEEDS CARE', '13.69% missing; these are IDs (333 distinct), not quantities. Missing may mean "no agent".'),
    'company': ('NEEDS CARE', '94.31% missing; IDs, not quantities. Likely reduce to a has-company flag or drop.'),
    'days_in_waiting_list': ('NEEDS CARE', 'LEAKAGE SUSPECT on timing: known only after the waiting period. Waiting>0 -> 63.8% cancel.'),
    'customer_type': ('USABLE', 'Known at booking. Four values.'),
    'adr': ('NEEDS CARE', 'Regression TARGET. As a feature for cancellation it is quoted at booking, but has min -6.38 and max 5400.'),
    'required_car_parking_spaces': ('LEAKAGE', 'All 7,416 bookings with 1+ spaces have 0 cancellations (exactly 0.00%): parking is only recorded for guests who arrive.'),
    'total_of_special_requests': ('NEEDS CARE', 'Requests can be added after booking (timing suspect). 0 requests -> 47.7% cancel, 3+ -> 16.8%: a gradual pattern, not a perfect split.'),
    'reservation_status': ('LEAKAGE', 'Canceled/No-Show map exactly to is_canceled = 1. It IS the answer.'),
    'reservation_status_date': ('LEAKAGE', 'For Canceled rows it is the cancellation date; for Check-Out rows it equals departure date (99.96%).'),
}
original_cols = set(df.columns) - {'room_changed'}   # room_changed is a helper column we created in E3
assert set(verdict) == original_cols, original_cols ^ set(verdict)

dictionary = profile.copy()
dictionary['verdict'] = [verdict[c][0] for c in dictionary.index]
dictionary['reason'] = [verdict[c][1] for c in dictionary.index]
dictionary.index.name = 'column'
dictionary.to_csv('STEP_2_column_dictionary.csv')

print(dictionary['verdict'].value_counts().to_string())
dictionary[['verdict', 'reason']]""")

md("""## Summary of Step 2

- Real missing values exist in 4 columns only: `children` (4), `country` (488), `agent` (16,340), `company` (112,593).
- Hidden missing values (`Undefined`) exist in `meal`, `market_segment`, `distribution_channel`.
- **No-Show is counted as cancelled** in `is_canceled`.
- Leakage confirmed with evidence: `reservation_status`, `reservation_status_date`, `assigned_room_type`, `required_car_parking_spaces` (found in the re-audit).
- Leakage suspects to settle by ablation: `booking_changes`, `days_in_waiting_list`, `total_of_special_requests`.
- The single-column screen only caught `reservation_status`. The date leak hides in a relationship between columns (`gap` AUC 0.9998 vs 0.638 for the raw date), so logic and pair checks are essential. `assigned_room_type` is a partial leak (room_changed AUC 0.585): it is excluded because of timing and mechanism, not strength.
- Counter-intuitive pattern to investigate: `deposit_type = Non Refund` cancels 99.36% of the time.
- Oddities queued for Step 3: adr = -6.38 and 5400, adults up to 55, zero-night stays, zero-adult rows.""")
