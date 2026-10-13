"""
export_powerbi.py
Exports Power BI ready CSV files from the DuckDB database.

Run from the project root:
    python src/export_powerbi.py
"""

from pathlib import Path

import duckdb

DB_PATH = Path("data/magicbricks.duckdb")
OUT_DIR = Path("data/powerbi")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    sales_path = (OUT_DIR / "sales.csv").as_posix()
    con.execute(
        f"""
        COPY (
            SELECT
                property_id, city, locality, property_type, bhk, area_sqft,
                furnishing, bathrooms, balconies, property_status,
                distance_from_city_center_km, floor_no, posted_by,
                posted_date, posted_month, price_lakh, price_per_sqft,
                is_price_outlier
            FROM listings
            WHERE transaction_type = 'Sale'
        ) TO '{sales_path}' (HEADER, DELIMITER ',')
        """
    )

    amen_path = (OUT_DIR / "amenities.csv").as_posix()
    con.execute(
        f"""
        COPY (
            SELECT a.property_id, a.amenity
            FROM amenities a
            JOIN listings l ON a.property_id = l.property_id
            WHERE l.transaction_type = 'Sale'
        ) TO '{amen_path}' (HEADER, DELIMITER ',')
        """
    )

    n_sales = con.execute(
        "SELECT COUNT(*) FROM listings WHERE transaction_type = 'Sale'"
    ).fetchone()[0]
    print(f"sales.csv: {n_sales} rows")
    print(f"Files saved in {OUT_DIR.resolve()}")
    con.close()


if __name__ == "__main__":
    main()