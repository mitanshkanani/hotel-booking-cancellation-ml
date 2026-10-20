"""STEP 1 - First look at the Hotel Booking data.

Goal: only LOOK at the data (no cleaning, no modelling).
Checks: shape, column types, a few raw rows, and how balanced the target is.

Run from the project root:
    python data_exploration/STEP_1_First_Look/STEP_1_first_look.py
"""
from pathlib import Path

import pandas as pd

# Resolve the CSV relative to this file so the script works from any folder.
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "hotel_bookings.csv"

pd.set_option("display.width", 200)       # wider printing so columns do not wrap
pd.set_option("display.max_columns", 50)  # show all columns instead of "..."

df = pd.read_csv(DATA_PATH)  # load CSV into a DataFrame (one row = one booking)

print("SHAPE:", df.shape)  # (rows, columns) - cheapest sanity check

print("\nDTYPES:")
print(df.dtypes.to_string())  # how pandas interpreted each column

print("\nFIRST 3 ROWS (transposed):")
print(df.head(3).T.to_string())  # .T so the 32 column names run down the page

print("\nTARGET is_canceled counts:")
print(df["is_canceled"].value_counts().to_string())
print(df["is_canceled"].value_counts(normalize=True).round(4).to_string())

# Baseline: accuracy of a model that always predicts "not cancelled".
baseline_accuracy = (df["is_canceled"] == 0).mean()
print(f"\nMajority-class baseline accuracy: {baseline_accuracy:.4f}")
