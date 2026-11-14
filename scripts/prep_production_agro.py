import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

from pathlib import Path

class DataPrep:
    def __init__(self):
        # nacteni CSV
        self.data_path = Path("data/training/production")

        self.fresh = pd.read_csv(self.data_path / "papriky-fresh.csv")
        self.dry = pd.read_csv(self.data_path / "papriky-dry.csv")

        self.productionData = pd.read_csv(self.data_path / "papriky-production.csv") if (self.data_path / "papriky-production.csv").exists() else self.doDataPrep()

        # zobraz prvnich 5 radku
    def doDataPrep(self):
        fresh = self.fresh.copy()
        dry = self.dry.copy()

        print("\nFresh peppers:")
        print(fresh.head())

        print("\nDry peppers:")
        print(dry.head())


        # zkontroluj, ze maji stejne sloupce
        print("Same columns:", fresh.columns.equals(dry.columns))
        # Ano, maji

        #fresh.info()
        #dry.info()

        # pocet unikatnich hodnot ve sloupcich

        print("\nFresh – number of unique values:")
        print(fresh.nunique())

        print("\nDry – number of unique values:")
        print(dry.nunique())


        # souhrn informaci o unikatnich hodnotach sloupcu

        fresh_summary = self.analyze_columns(fresh)
        dry_summary = self.analyze_columns(dry)

        print("\nFresh:")
        print(fresh_summary)

        print("\nDry:")
        print(dry_summary)
        """ 

        # overeni jednoznacneho mapovani dvojic sloupcu
        """
        # odstraneni nepotrebnych sloupcu
        # K odstranění:
        columns_to_drop = [
            "Domain Code",
            "Domain",
            "Element Code",
            "Item Code (CPC)",
            "Year Code",
            "Note"
        ]

        # drop země které neexistují
        old = ["China", "USSR", "Yugoslav SFR", "Czechoslovakia", "Serbia and Montenegro",
       "Ethiopia PDR", "Sudan (former)", "Belgium-Luxembourg"]

        fresh = fresh[fresh["Area"].isin(old) == False]
        dry = dry[dry["Area"].isin(old) == False]

        fresh_clean = fresh.drop(columns=columns_to_drop)
        dry_clean = dry.drop(columns=columns_to_drop)

        print("Fresh peppers:", fresh_clean.shape)
        print("Dry peppers:", dry_clean.shape)

        # Konzistence casovych rad

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
                print(f"Nonconsistent {area}: {years}")

        # Indonesia v datasetu dry peppers – chybi rok 1990.

        # prejmenovani sloupcu
        column_mapping = {
            "Area Code (M49)": "area_code",
            "Area": "area",
            "Element": "element",
            "Item": "peppers",
            "Year": "year",
            "Unit": "unit",
            "Value": "value",
            "Flag":"flag_prod",
            "Flag Description":"flag_prod_desc",
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

        print("Concating datasets...")

        # spojeni datasetu
        peppers = pd.concat(
            [fresh_clean, dry_clean],
            ignore_index=True
        )

        print("Combined dataset:", peppers.shape)
        print(peppers.head())

        # pivotovani elementu do sloupcu
        peppers_pivot = peppers.pivot(
            index=["flag_prod", "flag_prod_desc", "area_code", "area", "peppers", "year"],
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

        value_columns = ["area_harvested", "production", "yield"]

        for pepper_type, df in peppers_pivot.groupby("peppers"):
            missing_count = df[value_columns].isna().sum(axis=1)
            incomplete = df[missing_count == 1]

            print(f"\n{pepper_type.upper()} PEPPERS")
            print(incomplete[value_columns].isna().sum())


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

        print(peppers_pivot.head(10))
        
        # zahazuji anomálie, kde je area_harvested <= 0 a production > 0
        
        """
                flag  flag_desc                            area          peppers  year  area_harvested  production  yield  
        A     Official value                       Mali          dry      1964  0.0             1300.00     inf        1
                                                Sweden        fresh    2018  0.0             40.00       inf        1
                                                                        2019  0.0             40.00       inf        1
                                                                        2020  0.0             40.00       inf        1
                                                                        2021  0.0             50.00       inf        1
                                                                        2022  0.0             50.00       inf        1
                                                                        2023  0.0             40.00       inf        1
                                                                        2024  0.0             30.00       inf        1
        E     Estimated value                      Cook Islands  fresh    1992  0.0             2.00        10000.0    1
                                                                        1993  0.0             3.00        10000.0    1
                                                                        1995  0.0             1.00        10000.0    1
                                                                        2004  0.0             1.00        10000.0    1
                                                                        2005  0.0             1.00        10000.0    1
                                                                        2006  0.0             1.00        10000.0    1
                                                                        2007  0.0             2.00        10000.0    1
        I     Value imputed by a receiving agency  Cook Islands  fresh    2022  0.0             0.51        inf        1
                                                                        2023  0.0             0.47        inf        1
                                                                        2024  0.0             0.47        inf        1
        """
        peppers_pivot = peppers_pivot[(peppers_pivot["area_harvested"] != 0) & (peppers_pivot["production"] > 0)]
        
        climate_data = pd.read_csv("data/training/production/temperatureChange.csv")
        columns_to_drop = ["Domain Code", "Domain", "Area Code (M49)", "Element Code", "Months Code", "Months", "Year Code"]
        climate_data = climate_data.drop(columns=columns_to_drop)

        climate_data = climate_data.rename(columns={
            "Area": "area",
            "Year": "year",
            "Value": "climate_value",
            "Flag": "climate_flag",
            "Flag Description": "climate_flag_desc",
        })
        climate_data = climate_data.pivot_table(
            index=["area", "year"],
            columns="Element",
            values=["climate_value", "climate_flag", "climate_flag_desc"],
            aggfunc="first",
        )
        climate_data.columns = [
            f"{metric}_{element.lower().replace(' ', '_')}"
            for metric, element in climate_data.columns
        ]
        climate_data = climate_data.reset_index()
        
        print(climate_data.head())
        
        final_data = pd.merge(
            peppers_pivot,
            climate_data,
            how="left",
            on=["area", "year"],
        )
        print(final_data.head())
        
        prices = pd.read_csv("data/training/production/pricePeppers.csv")
        columns_to_drop = ["Domain Code", "Domain", "Area Code (M49)", "Element Code", "Year Code", "Item Code (CPC)", "Year Code", "Months Code", "Months"]
        prices = prices.drop(columns=columns_to_drop)
        prices["Item"] = prices["Item"].replace({
            "Chillies and peppers, dry (Capsicum spp., Pimenta spp.), raw": "dry",
            "Chillies and peppers, green (Capsicum spp. and Pimenta spp.)": "fresh",
        })
        
        #rename columns 
        prices = prices.rename(columns={
            "Area": "area",
            "Element": "price_element",
            "Item": "peppers",
            "Year": "year",
            "Unit": "price_unit",
            "Value": "price_value",
            "Flag": "price_flag",
            "Flag Description": "price_flag_desc",
        })
        
        #print(prices[["price_element", "price_unit", "price_flag_desc"]].value_counts().reset_index(name="count"))
        # show values that are Time series and Value from external organization
        
        
        prices = prices[(prices["price_flag_desc"] != "Time series break") | (prices["price_flag_desc"] != "Value from external organization")]


        # price elementy spočteny, 
        print(prices["price_element"].value_counts())

        # volíme ten nejvíc Producer Price Index (PPI)
        prices = prices[prices["price_element"] == "Producer Price Index (2014-2016 = 100)"]
        
        final_data = pd.merge(
            final_data,
            prices,
            how="left",
            on=["area", "year", "peppers"],
        )   
        
        copy_data = final_data[["area", "peppers", "year", "yield", "price_value", "climate_value_standard_deviation", "climate_value_temperature_change"]].copy()
        copy_data["year"] += 1
        
        copy_data = copy_data.rename(columns={
            "yield": "yield_prev_year",
            "price_value": "price_value_prev_year",
            "climate_value_standard_deviation": "climate_value_standard_deviation_prev_year",
            "climate_value_temperature_change": "climate_value_temperature_change_prev_year",
        })
        
        final_data = pd.merge(
            final_data,
            copy_data,
            how="left",
            on=["area", "peppers", "year"],
        )
        
        final_data = final_data.dropna(subset=["yield_prev_year"]) 
        
        final_data["production_rise"] = (final_data["yield"] > final_data["yield_prev_year"]).astype(int)
        
        # print(final_data["production_rise"].value_counts(normalize=True))
        # ulozit data do CSV
        final_data.to_csv(self.data_path / "papriky-production.csv", index=False)

        return final_data

    def analyze_columns(self,df):
            summary = pd.DataFrame({
                "Unique values": df.nunique(dropna=False),
                "Missing values": df.isna().sum()
            })

            summary["Constant (100%)"] = (
                (summary["Unique values"] == 1) &
                (summary["Missing values"] == 0)
            )

            return summary
if __name__ == "__main__":
    prep = DataPrep()
