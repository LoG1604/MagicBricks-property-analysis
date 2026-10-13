import duckdb

con = duckdb.connect("data/magicbricks.duckdb", read_only=True)

print("Clean table, most common rent values:")
print(
    con.execute(
        """
        SELECT monthly_rent, COUNT(*) AS n
        FROM listings
        WHERE transaction_type = 'Rent'
        GROUP BY 1 ORDER BY n DESC LIMIT 10
        """
    ).df().to_string(index=False)
)

print("\nClean table, rent range:")
print(
    con.execute(
        """
        SELECT MIN(monthly_rent) AS min_rent,
               MAX(monthly_rent) AS max_rent,
               COUNT(DISTINCT monthly_rent) AS distinct_values
        FROM listings
        WHERE transaction_type = 'Rent'
        """
    ).df().to_string(index=False)
)

print("\nRaw CSV, most common Per Month prices:")
print(
    con.execute(
        """
        SELECT Price, COUNT(*) AS n
        FROM read_csv_auto('data/raw/magicbricks.csv')
        WHERE Price_Unit = 'Per Month'
        GROUP BY 1 ORDER BY n DESC LIMIT 10
        """
    ).df().to_string(index=False)
)