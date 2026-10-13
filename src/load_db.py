"""
load_db.py
Loads the clean CSV into a DuckDB database and builds an amenities table.

Run from the project root:
    python src/load_db.py
"""

from pathlib import Path

import duckdb

CSV_PATH = Path("data/clean/listings_clean.csv")
DB_PATH = Path("data/magicbricks.duckdb")


def main():
    con = duckdb.connect(str(DB_PATH))

    # Main table
    con.execute("DROP TABLE IF EXISTS listings")
    con.execute(
        f"""
        CREATE TABLE listings AS
        SELECT * FROM read_csv_auto('{CSV_PATH.as_posix()}')
        """
    )

    # One row per property per amenity (makes amenity analysis easy in SQL)
    con.execute("DROP TABLE IF EXISTS amenities")
    con.execute(
        """
        CREATE TABLE amenities AS
        SELECT
            property_id,
            trim(unnest(string_split(amenities, ','))) AS amenity
        FROM listings
        WHERE amenities <> 'None'
        """
    )

    # Quick checks
    print("listings rows:", con.execute("SELECT COUNT(*) FROM listings").fetchone()[0])
    print("amenities rows:", con.execute("SELECT COUNT(*) FROM amenities").fetchone()[0])

    print("\nlistings schema:")
    print(con.execute("DESCRIBE listings").df().to_string(index=False))

    print("\nSale vs rent:")
    print(
        con.execute(
            "SELECT transaction_type, COUNT(*) AS n FROM listings GROUP BY 1"
        ).df().to_string(index=False)
    )

    print("\nTop amenities:")
    print(
        con.execute(
            """
            SELECT amenity, COUNT(*) AS n
            FROM amenities GROUP BY 1 ORDER BY n DESC LIMIT 10
            """
        ).df().to_string(index=False)
    )

    con.close()
    print(f"\nDatabase saved to {DB_PATH.resolve()}")


if __name__ == "__main__":
    main()