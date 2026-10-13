"""
clean.py
Cleans the raw MagicBricks listings and writes tidy CSVs to data/clean/.

Run from the project root:
    python src/clean.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path("data/raw/magicbricks.csv")
OUT_DIR = Path("data/clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Sanity limits (change these if your exploration says otherwise)
MIN_AREA, MAX_AREA = 200, 10_000
MAX_BHK = 6
MAX_BATHROOMS = 8


def log_step(label, before, after):
    print(f"{label:<45} {before:>5} -> {after:>5}  (removed {before - after})")


def main():
    df = pd.read_csv(RAW_PATH)
    print(f"Raw shape: {df.shape}\n")

    # 1. Column names to snake_case
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    )

    # 2. Duplicates
    n = len(df)
    df = df.drop_duplicates()
    log_step("Drop fully duplicated rows", n, len(df))

    n = len(df)
    df = df.drop_duplicates(subset="property_id", keep="first")
    log_step("Drop repeated property_id", n, len(df))

    # 3. Text standardization
    text_cols = [
        "city", "locality", "property_type", "furnishing",
        "transaction_type", "property_status", "posted_by",
    ]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()

    df["city"] = df["city"].str.title()
    df["furnishing"] = df["furnishing"].str.title()

    # 4. Price: strip the rupee sign, the word Lakh and commas
    df["price"] = pd.to_numeric(
        df["price"].astype("string").str.replace(r"[^\d.]", "", regex=True),
        errors="coerce",
    )

    n = len(df)
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]
    log_step("Drop rows with missing or zero price", n, len(df))

    # 5. Area: impossible values
    n = len(df)
    df = df[df["area_sqft"].between(MIN_AREA, MAX_AREA)]
    log_step(f"Drop area outside {MIN_AREA}-{MAX_AREA} sqft", n, len(df))

    # 6. BHK, bathrooms: set impossible values to NaN (keep the row)
    studio = df["property_type"].eq("Studio Apartment")
    bad_bhk = ((df["bhk"] == 0) & ~studio) | (df["bhk"] > MAX_BHK)
    print(f"\nBHK set to NaN (invalid): {int(bad_bhk.sum())}")
    df.loc[bad_bhk, "bhk"] = np.nan

    bad_bath = (df["bathrooms"] < 0) | (df["bathrooms"] > MAX_BATHROOMS)
    print(f"Bathrooms set to NaN (invalid): {int(bad_bath.sum())}")
    df.loc[bad_bath, "bathrooms"] = np.nan

    # 7. Dates: parse and drop future dates
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
    today = pd.Timestamp.today().normalize()
    n = len(df)
    df = df[df["posted_date"].notna() & (df["posted_date"] <= today)]
    log_step("Drop bad or future posted dates", n, len(df))

    # 8. Fill missing categories with clear labels
    df["locality"] = df["locality"].fillna("Unknown")
    df["furnishing"] = df["furnishing"].fillna("Unknown")
    df["posted_by"] = df["posted_by"].fillna("Unknown")
    df["amenities"] = df["amenities"].fillna("None")

    # 9. Split price by transaction type (sale and rent are not comparable)
    df["price_lakh"] = np.where(df["transaction_type"] == "Sale", df["price"], np.nan)
    df["monthly_rent"] = np.where(df["transaction_type"] == "Rent", df["price"], np.nan)

    # Sale price per sqft (price is in Lakh, 1 Lakh = 100,000 rupees)
    df["price_per_sqft"] = np.where(
        df["transaction_type"] == "Sale",
        df["price_lakh"] * 100_000 / df["area_sqft"],
        df["monthly_rent"] / df["area_sqft"],
    )

    # 10. Flag outliers (kept in data, filter them in SQL or the dashboard)
    grp = df.groupby("transaction_type")["price_per_sqft"]
    q1 = grp.transform(lambda s: s.quantile(0.25))
    q3 = grp.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    df["is_price_outlier"] = (df["price_per_sqft"] < q1 - 3 * iqr) | (
        df["price_per_sqft"] > q3 + 3 * iqr
    )
    print(f"Price outliers flagged: {int(df['is_price_outlier'].sum())}")

    # 11. Helpful date columns
    df["posted_month"] = df["posted_date"].dt.to_period("M").astype(str)

    # 12. Tidy column order and save
    df = df.drop(columns=["price"])
    df = df.sort_values("property_id").reset_index(drop=True)

    df.to_csv(OUT_DIR / "listings_clean.csv", index=False)
    df[df["transaction_type"] == "Sale"].to_csv(OUT_DIR / "sale_clean.csv", index=False)
    df[df["transaction_type"] == "Rent"].to_csv(OUT_DIR / "rent_clean.csv", index=False)

    print(f"\nFinal shape: {df.shape}")
    print("\nRemaining nulls:")
    print(df.isnull().sum()[df.isnull().sum() > 0].to_string())
    print(f"\nSaved to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()