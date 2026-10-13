"""
run_queries.py
Runs every query in sql/queries.sql against the DuckDB database and prints the results.

Run from the project root:
    python src/run_queries.py
"""

import re
from pathlib import Path

import duckdb

DB_PATH = Path("data/magicbricks.duckdb")
SQL_PATH = Path("sql/queries.sql")


def main():
    text = SQL_PATH.read_text(encoding="utf-8")

    # Split on lines that start with "-- Q1", "-- Q2", and so on
    parts = re.split(r"^-- (Q\d+.*)$", text, flags=re.MULTILINE)
    titles = parts[1::2]
    queries = parts[2::2]

    con = duckdb.connect(str(DB_PATH), read_only=True)

    for title, sql in zip(titles, queries):
        sql = sql.strip().rstrip(";")
        print("=" * 70)
        print(title)
        print("=" * 70)
        result = con.execute(sql).df()
        print(result.to_string(index=False))
        print()

    con.close()


if __name__ == "__main__":
    main()