import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

from pathlib import Path

# nacteni CSV
data_path = Path("data/training/production")

fresh = pd.read_csv(data_path / "papriky-fresh.csv")
dry = pd.read_csv(data_path / "papriky-dry.csv")

# zobraz prvnich 5 radku
"""
print("\nFresh peppers:")
print(fresh.head())

print("\nDry peppers:")
print(dry.head())
"""

# zkontroluj, ze maji stejne sloupce
#print("Same columns:", fresh.columns.equals(dry.columns))
# Ano, maji

#fresh.info()
#dry.info()

# pocet unikatnich hodnot ve sloupcich
"""
print("\nFresh – number of unique values:")
print(fresh.nunique())

print("\nDry – number of unique values:")
print(dry.nunique())
"""

# souhrn informaci o unikatnich hodnotach sloupcu
"""
def analyze_columns(df):
    summary = pd.DataFrame({
        "Unique values": df.nunique(dropna=False),
        "Missing values": df.isna().sum()
    })

    summary["Constant (100%)"] = (
        (summary["Unique values"] == 1) &
        (summary["Missing values"] == 0)
    )

    return summary


fresh_summary = analyze_columns(fresh)
dry_summary = analyze_columns(dry)

print("\nFresh:")
print(fresh_summary)

print("\nDry:")
print(dry_summary)
""" 

# overeni jednoznacneho mapovani dvojic sloupcu
"""
def check_mapping(df, column_a, column_b):
    # Check how many unique values of B belong to each value of A
    a_to_b = df.groupby(column_a)[column_b].nunique()

    # Check how many unique values of A belong to each value of B
    b_to_a = df.groupby(column_b)[column_a].nunique()

    print(f"\nMapping: {column_a} -> {column_b}")
    print("Maximum unique values:", a_to_b.max())
    print("Is mapping 1:1:", a_to_b.max() == 1 and b_to_a.max() == 1)

    if a_to_b.max() > 1:
        print("\nValues of A mapped to multiple values of B:")
        print(a_to_b[a_to_b > 1])

    if b_to_a.max() > 1:
        print("\nValues of B mapped to multiple values of A:")
        print(b_to_a[b_to_a > 1])

print("=== FRESH PEPPERS ===")

check_mapping(fresh, "Area Code (M49)", "Area")
check_mapping(fresh, "Element Code", "Element")
check_mapping(fresh, "Year Code", "Year")


print("\n=== DRY PEPPERS ===")

check_mapping(dry, "Area Code (M49)", "Area")
check_mapping(dry, "Element Code", "Element")
check_mapping(dry, "Year Code", "Year")
"""
# vsechny sloupce maji jednoznacne mapovani 

# uprava dat 

# odstraneni nepotrebnych sloupcu
# K odstranění:
columns_to_drop = [
    "Domain Code",
    "Domain",
    "Element Code",
    "Item Code (CPC)",
    "Year Code",
    "Flag", 
    "Flag Description", 
    "Note"
]

fresh_clean = fresh.drop(columns=columns_to_drop)
dry_clean = dry.drop(columns=columns_to_drop)

print("Fresh peppers:", fresh_clean.shape)
print("Dry peppers:", dry_clean.shape)

# Konzistence casovych rad 
"""
for name, df in [("Fresh", fresh_clean), ("Dry", dry_clean)]:
    missing_years = []

    for area, group in df.groupby("Area"):
        years = set(group["Year"])
        expected_years = set(range(group["Year"].min(), group["Year"].max() + 1))

        missing = sorted(expected_years - years)

        if missing:
            missing_years.append((area, missing))

    print(f"\n{name.upper()} PEPPERS")
    for area, years in missing_years:
        print(f"{area}: {years}")
"""
# Indonesia v datasetu dry peppers – chybi rok 1990. 

# prejmenovani sloupcu
column_mapping = {
    "Area Code (M49)": "area_code",
    "Area": "area",
    "Element": "element",
    "Item": "peppers",
    "Year": "year",
    "Unit": "unit",
    "Value": "value"
}

fresh_clean = fresh_clean.rename(columns=column_mapping)
dry_clean = dry_clean.rename(columns=column_mapping)

# prejmenovani hodnot 
element_mapping = {
    "Production": "production",
    "Area harvested": "area_harvested",
    "Yield": "yield"
}

for df in [fresh_clean, dry_clean]:
    df["element"] = df["element"].replace(element_mapping)

fresh_clean["peppers"] = "fresh"
dry_clean["peppers"] = "dry" 

"""
print("Fresh peppers:")
print(fresh_clean.head())
print(fresh_clean.dtypes)

print("\nDry peppers:")
print(dry_clean.head())
print(dry_clean.dtypes)
"""

# spojeni datasetu
peppers = pd.concat(
    [fresh_clean, dry_clean],
    ignore_index=True
)

#print("Combined dataset:", peppers.shape)
#print(peppers.head())

# pivotovani elementu do sloupcu
peppers_pivot = peppers.pivot(
    index=["area_code", "area", "peppers", "year"],
    columns="element",
    values="value"
).reset_index()

# odstrani element z nazvu sloupce indexu
peppers_pivot.columns.name = None

print("Shape:", peppers_pivot.shape)
print(peppers_pivot.head())
print(peppers_pivot.dtypes)

# chybejici hodnoty
# celkove na element 
value_columns = ["area_harvested", "production", "yield"]

for pepper_type, df in peppers_pivot.groupby("peppers"):
    print(f"\n{pepper_type.upper()} PEPPERS")

    missing = df[value_columns].isna().agg(["sum", "mean"]).T
    missing.columns = ["Missing", "Missing (%)"]
    missing["Missing (%)"] = (missing["Missing (%)"] * 100).round(2)

    print(missing)

# jak jsou na tom jednotlive radky – kolik elementu chybi

value_columns = ["area_harvested", "production", "yield"]

for pepper_type, df in peppers_pivot.groupby("peppers"):
    missing_count = df[value_columns].isna().sum(axis=1)

    print(f"\n{pepper_type.upper()} PEPPERS")
    print(missing_count.value_counts().sort_index().to_string())

# 0 - vsechno vyplnene
# 1 - chybi 1 element
# 2 - chybi 2 elementy
# 3 - chybi vsechny 3 elementy

# pokud chybi 1 element - ktery? 
"""
value_columns = ["area_harvested", "production", "yield"]

for pepper_type, df in peppers_pivot.groupby("peppers"):
    missing_count = df[value_columns].isna().sum(axis=1)
    incomplete = df[missing_count == 1]

    print(f"\n{pepper_type.upper()} PEPPERS")
    print(incomplete[value_columns].isna().sum())
"""

# chybi vzdy yield 

# pokud chybi 1 element (yield), muzeme jej dopocitat
# pokud by byl problem data leakage, tak nepouzit
missing_yield = (
    peppers_pivot["yield"].isna()
    & peppers_pivot["production"].notna()
    & peppers_pivot["area_harvested"].notna()
)

peppers_pivot.loc[missing_yield, "yield"] = (
    peppers_pivot.loc[missing_yield, "production"] * 1000
    / peppers_pivot.loc[missing_yield, "area_harvested"]
)
#print("Recalculated yields:", missing_yield.sum())

value_columns = ["area_harvested", "production", "yield"]

for pepper_type, df in peppers_pivot.groupby("peppers"):
    print(f"\n{pepper_type.upper()} PEPPERS")
    print(df[value_columns].isna().sum())

# hotovo

# --- OPTIONAL upravy ---

# odstranime area code
peppers_pivot = peppers_pivot.drop(columns=["area_code"])

"""
# odstranime radky kde chybi vsechny 3 elementy
peppers_pivot = peppers_pivot.dropna(
    subset=["area_harvested", "production", "yield"],
    how="all"
)

# odstranime radky kde chybi alespon 1 element
peppers_pivot = peppers_pivot.dropna(
    subset=["area_harvested", "production", "yield"],
    how="any"
)
"""

print(peppers_pivot.head(10))