"""
build_pbip_model.py
Writes the sales table (Power Query source + DAX measures) into a Power BI
Project semantic model, so you only have to build the visuals.

Before running:
  1. python src/export_powerbi.py          (creates data/powerbi/sales.csv)
  2. Save an empty report from Power BI Desktop as a .pbip inside ./powerbi
     or ./data/powerbi, then close Power BI Desktop.

Run from the project root:
    python src/build_pbip_model.py
"""

import sys
import uuid
from pathlib import Path

CSV_PATH = Path("data/powerbi/sales.csv").resolve()
SEARCH_DIRS = [Path("powerbi"), Path("data/powerbi")]

# (name, TMDL dataType, Power Query type)
COLUMNS = [
    ("property_id", "string", "type text"),
    ("city", "string", "type text"),
    ("locality", "string", "type text"),
    ("property_type", "string", "type text"),
    ("bhk", "double", "type number"),
    ("area_sqft", "int64", "Int64.Type"),
    ("furnishing", "string", "type text"),
    ("bathrooms", "double", "type number"),
    ("balconies", "double", "type number"),
    ("property_status", "string", "type text"),
    ("distance_from_city_center_km", "double", "type number"),
    ("floor_no", "int64", "Int64.Type"),
    ("posted_by", "string", "type text"),
    ("posted_date", "dateTime", "type date"),
    ("posted_month", "string", "type text"),
    ("price_lakh", "double", "type number"),
    ("price_per_sqft", "double", "type number"),
    ("is_price_outlier", "boolean", "type logical"),
]

# (measure name, DAX, format string)
MEASURES = [
    ("Listings", "COUNTROWS(sales)", "#,0"),
    ("Median Price Lakh", "MEDIAN(sales[price_lakh])", "#,0.0"),
    ("Median Price per Sqft", "MEDIAN(sales[price_per_sqft])", "#,0"),
    ("Median Area", "MEDIAN(sales[area_sqft])", "#,0"),
]


def build_table_tmdl():
    t = "\t"
    lines = ["table sales", f"{t}lineageTag: {uuid.uuid4()}", ""]

    for name, dax, fmt in MEASURES:
        lines.append(f"{t}measure '{name}' = {dax}")
        lines.append(f"{t}{t}formatString: {fmt}")
        lines.append(f"{t}{t}lineageTag: {uuid.uuid4()}")
        lines.append("")

    for name, dtype, _ in COLUMNS:
        lines.append(f"{t}column {name}")
        lines.append(f"{t}{t}dataType: {dtype}")
        if dtype == "dateTime":
            lines.append(f"{t}{t}formatString: Long Date")
        lines.append(f"{t}{t}lineageTag: {uuid.uuid4()}")
        lines.append(f"{t}{t}summarizeBy: none")
        lines.append(f"{t}{t}sourceColumn: {name}")
        lines.append("")

    type_list = ", ".join(f'{{"{n}", {m}}}' for n, _, m in COLUMNS)
    csv_text = str(CSV_PATH).replace('"', '""')

    lines.append(f"{t}partition sales = m")
    lines.append(f"{t}{t}mode: import")
    lines.append(f"{t}{t}source =")
    m_lines = [
        "let",
        f'    Source = Csv.Document(File.Contents("{csv_text}"), '
        '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{type_list}}}, "en-US")',
        "in",
        "    Typed",
    ]
    for ml in m_lines:
        lines.append(f"{t}{t}{t}{t}{ml}")
    lines.append("")
    return "\n".join(lines)


def main():
    if not CSV_PATH.exists():
        sys.exit(f"Missing {CSV_PATH}. Run python src/export_powerbi.py first.")

    models = []
    for folder in SEARCH_DIRS:
        models += list(folder.glob("*.SemanticModel"))
    if not models:
        sys.exit(
            "No *.SemanticModel folder found in ./powerbi or ./data/powerbi. "
            "Save an empty report from Power BI Desktop as a .pbip inside one "
            "of those folders first."
        )
    model_dir = models[0]
    definition = model_dir / "definition"

    if not definition.exists():
        sys.exit(
            f"{model_dir} has no 'definition' folder (TMDL format). "
            "It may be using model.bim instead. Paste me the folder contents."
        )

    tables_dir = definition / "tables"
    tables_dir.mkdir(exist_ok=True)
    (tables_dir / "sales.tmdl").write_text(
        build_table_tmdl(), encoding="utf-8", newline="\n"
    )

    # Register the table in model.tmdl if it is not there yet
    model_file = definition / "model.tmdl"
    if model_file.exists():
        text = model_file.read_text(encoding="utf-8")
        if "ref table sales" not in text:
            text = text.rstrip("\n") + "\n\nref table sales\n"
            model_file.write_text(text, encoding="utf-8", newline="\n")
            print("Added 'ref table sales' to model.tmdl")

    print(f"Wrote {tables_dir / 'sales.tmdl'}")
    print(f"CSV source: {CSV_PATH}")
    print("Now open the .pbip file in Power BI Desktop.")


if __name__ == "__main__":
    main()