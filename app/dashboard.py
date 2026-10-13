"""
dashboard.py
Interactive Streamlit dashboard on top of the MagicBricks DuckDB database.

Run from the project root:
    streamlit run app/dashboard.py
"""

from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "magicbricks.duckdb"

st.set_page_config(page_title="MagicBricks Property Analysis", layout="wide")


@st.cache_data
def load_sales():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        "SELECT * FROM listings WHERE transaction_type = 'Sale'"
    ).df()
    con.close()
    return df


df = load_sales()

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Filters")

cities = sorted(df["city"].unique())
sel_cities = st.sidebar.multiselect("City", cities, default=cities)

types = sorted(df["property_type"].unique())
sel_types = st.sidebar.multiselect("Property type", types, default=types)

bhks = sorted(df["bhk"].dropna().astype(int).unique())
sel_bhks = st.sidebar.multiselect("BHK", bhks, default=bhks)

statuses = sorted(df["property_status"].unique())
sel_status = st.sidebar.multiselect("Property status", statuses, default=statuses)

furn = sorted(df["furnishing"].unique())
sel_furn = st.sidebar.multiselect("Furnishing", furn, default=furn)

p_min, p_max = float(df["price_lakh"].min()), float(df["price_lakh"].max())
sel_price = st.sidebar.slider(
    "Price (Lakh)", p_min, p_max, (p_min, p_max)
)

hide_outliers = st.sidebar.checkbox("Hide price outliers", value=True)

# ---------------------------------------------------------------- filtering
f = df[
    df["city"].isin(sel_cities)
    & df["property_type"].isin(sel_types)
    & df["bhk"].isin(sel_bhks)
    & df["property_status"].isin(sel_status)
    & df["furnishing"].isin(sel_furn)
    & df["price_lakh"].between(*sel_price)
]
if hide_outliers:
    f = f[~f["is_price_outlier"]]

st.title("MagicBricks Property Analysis")
st.caption("Sale listings across 10 Indian cities. Use the filters on the left.")

if f.empty:
    st.warning("No listings match these filters. Try widening them.")
    st.stop()

# ---------------------------------------------------------------- KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Listings", f"{len(f):,}")
k2.metric("Median price", f"{f['price_lakh'].median():,.0f} Lakh")
k3.metric("Median price / sqft", f"{f['price_per_sqft'].median():,.0f}")
k4.metric("Median area", f"{f['area_sqft'].median():,.0f} sqft")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Localities", "Trend", "Data notes"]
)

# ---------------------------------------------------------------- overview
with tab1:
    c1, c2 = st.columns(2)

    by_city = (
        f.groupby("city")["price_per_sqft"].median().round().reset_index()
        .sort_values("price_per_sqft", ascending=True)
    )
    fig = px.bar(
        by_city, x="price_per_sqft", y="city", orientation="h",
        title="Median price per sqft by city",
        labels={"price_per_sqft": "Price per sqft", "city": ""},
    )
    c1.plotly_chart(fig, use_container_width=True)

    by_status = (
        f.groupby("property_status")["price_per_sqft"].median().round().reset_index()
        .sort_values("price_per_sqft", ascending=False)
    )
    fig = px.bar(
        by_status, x="property_status", y="price_per_sqft",
        title="Median price per sqft by property status",
        labels={"price_per_sqft": "Price per sqft", "property_status": ""},
    )
    c2.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    fig = px.histogram(
        f, x="price_lakh", nbins=40, title="Price distribution",
        labels={"price_lakh": "Price (Lakh)"},
    )
    c3.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(
        f, x="area_sqft", y="price_lakh", color="city", opacity=0.6,
        title="Area vs price",
        labels={"area_sqft": "Area (sqft)", "price_lakh": "Price (Lakh)"},
    )
    c4.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- localities
with tab2:
    min_n = st.slider("Minimum listings per locality", 3, 20, 5)
    top_n = st.slider("Localities to show", 5, 25, 10)

    loc = (
        f[f["locality"] != "Unknown"]
        .groupby(["city", "locality"])
        .agg(
            listings=("property_id", "count"),
            median_price_per_sqft=("price_per_sqft", "median"),
            median_price_lakh=("price_lakh", "median"),
        )
        .reset_index()
    )
    loc = loc[loc["listings"] >= min_n].round(0)
    loc = loc.sort_values("median_price_per_sqft", ascending=False).head(top_n)

    if loc.empty:
        st.info("No localities meet the minimum listing count.")
    else:
        loc["label"] = loc["locality"] + " (" + loc["city"] + ")"
        fig = px.bar(
            loc.sort_values("median_price_per_sqft"),
            x="median_price_per_sqft", y="label", orientation="h",
            title="Most expensive localities (median price per sqft)",
            labels={"median_price_per_sqft": "Price per sqft", "label": ""},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            loc.drop(columns="label"), use_container_width=True, hide_index=True
        )

# ---------------------------------------------------------------- trend
with tab3:
    monthly = f.groupby("posted_month").size().reset_index(name="listings")
    monthly = monthly.sort_values("posted_month")
    # The last month in the data is incomplete, so leave it out
    if len(monthly) > 1:
        monthly = monthly.iloc[:-1]
    fig = px.line(
        monthly, x="posted_month", y="listings", markers=True,
        title="Listings posted per month",
        labels={"posted_month": "Month", "listings": "Listings"},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The latest month is left out because the data stops mid-month.")

# ---------------------------------------------------------------- notes
with tab4:
    st.subheader("What the data shows")
    st.markdown(
        """
- **City is the biggest price driver.** Mumbai is roughly 4x Lucknow per sqft.
- **Ready to Move and Resale** listings cost about 17% more per sqft than New Launch.
- **No clear effect** was found for BHK, distance from city center, who posted the
  listing, or amenities. Differences were small and inconsistent.
"""
    )
    st.subheader("Data cleaning")
    st.markdown(
        """
- Removed 20 duplicate rows and 15 rows with no price
- Removed 8 rows with impossible areas (under 200 or over 10,000 sqft)
- Fixed inconsistent city and furnishing spellings
- Set impossible BHK and bathroom values to missing
- Flagged 11 price outliers (hidden by default, toggle in the sidebar)
"""
    )
    st.subheader("Limitation")
    st.markdown(
        """
Rent listings were left out of the analysis. Every rent price in the source
file is exactly 5,000 per month, so it carries no real information.
"""
    )