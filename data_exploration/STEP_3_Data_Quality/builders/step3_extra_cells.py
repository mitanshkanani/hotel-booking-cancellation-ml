md("""## Part F - Looking at the actual rows behind the findings

Numbers can mislead; real rows show what is going on. First: the largest duplicate groups. If they look like one organisation booking many identical rooms,
the duplicates are real bookings, not copy errors.""")

code("""top = sizes.sort_values(ascending=False).head(6)
tf = top.index.to_frame(index=False)
tf['copies'] = top.values
tf['total_nights'] = tf['stays_in_weekend_nights'] + tf['stays_in_week_nights']
print(tf[['copies', 'hotel', 'market_segment', 'lead_time', 'arrival_date_year', 'arrival_date_month',
          'arrival_date_day_of_month', 'adults', 'total_nights', 'adr', 'is_canceled']].to_string(index=False))""")

md("""Second: the rows with implausible guest counts (5+ adults, 4+ children, 3+ babies).""")

code("""big_adults = df['adults'] >= 5
odd_kids = (df['children'] >= 4) | (df['babies'] >= 3)
print(df.loc[big_adults | odd_kids, ['hotel', 'market_segment', 'adults', 'children', 'babies', 'total_nights', 'adr',
                                     'is_canceled', 'reservation_status']].sort_values('adults', ascending=False).to_string())""")

md("""## Part G - Decisions and the cleaned dataset (v1)

**Row-removal rules** (only for rows that are impossible or meaningless, defined by the *values*, never by whether the booking was cancelled):

| Rule | Why |
|---|---|
| zero guests | a booking with nobody in it is not a real stay |
| zero nights | not an overnight stay; all have adr = 0, consistent with price = revenue / nights being undefined for 0 nights |
| negative adr | a price cannot be negative |
| adr = 5400 | ten times the next highest value: almost certainly an entry error |
| 5+ adults | all have adr = 0 and are all cancelled: placeholder-like records |
| 4+ children or 3+ babies | implausible counts |

Everything else stays. Statistical fixes (filling missing values, encoding, scaling) are NOT done here - they are done in Step 6 **after** the train/test split so the test set never influences them.""")

code("""zero_adr_pos_nights = (df['adr'] == 0) & (df['total_nights'] > 0)
rules = {
    'zero guests (adults+children+babies = 0)': df['total_guests'] == 0,
    'zero nights (weekend+week nights = 0)': df['total_nights'] == 0,
    'negative adr': df['adr'] < 0,
    'adr > 1000 (the 5400 row)': df['adr'] > 1000,
    'adults >= 5': big_adults,
    'children >= 4 or babies >= 3': odd_kids,
}
seen = pd.Series(False, index=df.index)
log_rows = []
for name, m in rules.items():
    new_rows = m & ~seen
    log_rows.append({'rule': name, 'rows_flagged': int(m.sum()), 'additional_unique_rows_removed': int(new_rows.sum())})
    seen |= m
removal_log = pd.DataFrame(log_rows)
drop_mask = seen
print(removal_log.to_string(index=False))
print(f'\\nTotal rows removed: {drop_mask.sum():,} of {len(df):,} ({drop_mask.mean():.2%})')
print('cancel rate - removed rows:', round(df.loc[drop_mask, 'is_canceled'].mean(), 4),
      '| kept rows:', round(df.loc[~drop_mask, 'is_canceled'].mean(), 4))

clean = df.loc[~drop_mask, ORIG]
out_csv = DATA.parent / 'hotel_bookings_clean_v1.csv'
clean.to_csv(out_csv, index=False)
removal_log.to_csv('STEP_3_row_removal_log.csv', index=False)
print(f'\\nclean_v1 saved: {len(clean):,} rows x {clean.shape[1]} columns -> {out_csv.name}')
print('cancel rate after cleaning:', round(clean['is_canceled'].mean(), 4))
print('regression rows (adr > 0):', f'{(clean["adr"] > 0).sum():,}', '| adr == 0 rows kept for classification only:', f'{(clean["adr"] == 0).sum():,}')

# sanity checks: none of the removed patterns remain
c_guests = clean['adults'] + clean['children'].fillna(0) + clean['babies']
c_nights = clean['stays_in_weekend_nights'] + clean['stays_in_week_nights']
assert (c_guests > 0).all() and (c_nights > 0).all() and (clean['adr'] >= 0).all() and (clean['adr'] <= 1000).all()
print('sanity checks passed')""")

code("""fig, ax = plt.subplots(figsize=(7.5, 3.4))
lab = removal_log['rule']
vals = removal_log['additional_unique_rows_removed']
y = np.arange(len(lab))[::-1]
ax.barh(y, vals, color='#D9822B')
ax.set_yticks(y)
ax.set_yticklabels(lab, fontsize=8)
for yi, v in zip(y, vals):
    ax.text(v + 8, yi, f'{v:,}', va='center', fontsize=9)
ax.set_xlim(0, vals.max() * 1.18)
ax.set_xlabel('rows removed (unique, after earlier rules)')
ax.set_title(f'Rows removed in Step 3: {drop_mask.sum():,} of {len(df):,} ({drop_mask.mean():.2%})')
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(FIG / 'step3_rows_removed_per_rule.svg')
plt.show()""")

md("""## Part H - The full decision table

Every issue found in Step 3, with the decision and the reason. "Applied in" says where the action actually happens.""")

code("""n_dup_rows = int(df[ORIG].duplicated().sum())
decisions = pd.DataFrame([
    ('Full-row duplicates (2nd+ copies)', n_dup_rows, 'KEEP all rows',
     'Concentrated in Groups (84% of rows) and Offline TA/TO (50%): looks like real batch bookings. Dropping would remove real behaviour. Risk: copies in both train and test inflate the score.',
     'Step 6: group-aware split (identical-feature bookings stay on one side); sensitivity test with duplicates dropped'),
    ('Feature-identical bookings with different outcomes', int(g.loc[g['n_labels'] > 1, 'size'].sum()), 'KEEP',
     'About 1.8% of rows: irreducible label noise that limits the best possible score.', 'Step 8: remember when judging model scores'),
    ('Zero guests', int(rules['zero guests (adults+children+babies = 0)'].sum()), 'DROP', 'Not a real stay.', 'Step 3 (clean_v1)'),
    ('Zero nights', int(rules['zero nights (weekend+week nights = 0)'].sum()), 'DROP', 'Not an overnight stay; adr = 0 for all (price undefined).', 'Step 3 (clean_v1)'),
    ('Negative adr', int(rules['negative adr'].sum()), 'DROP', 'Price cannot be negative.', 'Step 3 (clean_v1)'),
    ('adr = 5400', int(rules['adr > 1000 (the 5400 row)'].sum()), 'DROP', 'Ten times the next highest value.', 'Step 3 (clean_v1)'),
    ('5+ adults', int(big_adults.sum()), 'DROP', 'All adr = 0 and all cancelled: placeholder-like.', 'Step 3 (clean_v1)'),
    ('4+ children or 3+ babies', int(odd_kids.sum()), 'DROP', 'Implausible counts.', 'Step 3 (clean_v1)'),
    ('adr = 0 with nights > 0', int(zero_adr_pos_nights.sum()), 'KEEP for classification, EXCLUDE from regression',
     'Complementary segment: 91.5% of its rows have adr 0 (free stays by design). Others unexplained. A free stay is a real booking but not a price.', 'Step 6: regression uses adr > 0 only'),
    ('adults = 0 but children/babies present', int(((df['adults'] == 0) & (df['total_guests'] > 0)).sum()), 'KEEP',
     '0.19% of rows; low impact. Revisit if errors concentrate here.', '-'),
    ('adr > 300 (but not the 5400 row)', int(((df['adr'] > 300) & (df['adr'] < 1000)).sum()), 'KEEP',
     'Plausible peak or suite prices (99th percentile is about 250-280).', 'Step 8: RMSE is sensitive to these; consider log(adr)'),
    ('lead_time >= 500', int(thr['lead_time >= 500'].sum()), 'KEEP', 'Real, and a strong signal (85.7% cancel).', 'Step 6: maybe log or cap for linear models'),
    ('total_nights >= 15', int(thr['total_nights >= 15'].sum()), 'KEEP', 'Long stays are plausible.', '-'),
    ('days_in_waiting_list >= 200', int(thr['days_in_waiting_list >= 200'].sum()), 'KEEP', 'Plausible; the column is excluded from the main model anyway (Step 2).', '-'),
    ('Missing: company (94.31%)', int(df['company'].isna().sum()), 'PLAN: has_company flag', 'IDs; almost empty.', 'Step 6'),
    ('Missing: agent (13.69%)', int(df['agent'].isna().sum()), 'PLAN: category "no agent"', 'IDs; missing probably means no agent.', 'Step 6'),
    ('Missing: country (0.41%)', int(df['country'].isna().sum()), 'PLAN: category "Unknown"', 'Small gap.', 'Step 6'),
    ('Missing: children (4 rows)', int(df['children'].isna().sum()), 'PLAN: fill with 0', 'Median is 0; only 4 rows.', 'Step 6 (fit on training data only)'),
    ('Undefined: meal', int((df['meal'] == 'Undefined').sum()), 'PLAN: merge with SC', 'Documentation says both mean no meal package.', 'Step 6'),
    ('Undefined: market_segment, distribution_channel', int((df['market_segment'] == 'Undefined').sum() + (df['distribution_channel'] == 'Undefined').sum()),
     'PLAN: keep as its own category', 'Only a handful of rows.', 'Step 6'),
], columns=['issue', 'rows', 'decision', 'reason', 'applied_in'])
decisions.to_csv('STEP_3_quality_decisions.csv', index=False)
decisions[['issue', 'rows', 'decision']]""")

md("""## Summary of Step 3

- Rows removed (impossible or meaningless): see the removal log above. Result: `data/hotel_bookings_clean_v1.csv`.
- Duplicates are **kept** (they look like real group bookings) but need a group-aware train/test split in Step 6.
- adr = 0 rows are kept for classification but excluded from the regression task.
- Missing-value and Undefined handling is planned for Step 6 (after the split, to avoid leakage).""")
