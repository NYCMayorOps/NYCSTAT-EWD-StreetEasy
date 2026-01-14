import io
import zipfile
import requests
import pandas as pd

# Data source URLs
RENTAL_URL = "https://cdn-charts.streeteasy.com/rentals/All/rentalIndex_All.zip"
SALES_URL = "https://cdn-charts.streeteasy.com/sales/All/priceIndex_All.zip"

# Borough mapping
BOROUGH_MAP = {
    "Brooklyn": "BK",
    "Manhattan": "MN",
    "Queens": "QN",
    "NYC": "NYC",
}

BOROCODE_MAP = {
    "BK": 3,
    "MN": 1,
    "QN": 4,
    "NYC": "",
}


def download_and_extract_csv(url):
    """Download ZIP file and extract the CSV inside."""
    response = requests.get(url)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        csv_filename = z.namelist()[0]
        with z.open(csv_filename) as f:
            return pd.read_csv(f)


def transform_to_long(df, value_col_name):
    """Unpivot wide format to long format."""
    # Melt from wide to long
    df_long = df.melt(
        id_vars=["month"],
        var_name="borough_orig",
        value_name=value_col_name,
    )

    # Map borough names
    df_long["borough"] = df_long["borough_orig"].map(BOROUGH_MAP)

    # Add borocode
    df_long["borocode"] = df_long["borough"].map(BOROCODE_MAP)

    # Rename month to year_month
    df_long = df_long.rename(columns={"month": "year_month"})

    # Keep only needed columns
    return df_long[["year_month", "borough", "borocode", value_col_name]]


def main():
    # Download and extract both datasets
    print("Downloading rental index...")
    rental_df = download_and_extract_csv(RENTAL_URL)

    print("Downloading sales index...")
    sales_df = download_and_extract_csv(SALES_URL)

    # Transform to long format
    print("Transforming data...")
    rental_long = transform_to_long(rental_df, "rental_index")
    sales_long = transform_to_long(sales_df, "sales_index")

    # Merge on year_month and borough
    merged = pd.merge(
        sales_long,
        rental_long[["year_month", "borough", "rental_index"]],
        on=["year_month", "borough"],
        how="outer",
    )

    # Sort: year_month desc, then by borocode (with empty last)
    merged["borocode_sort"] = merged["borocode"].apply(lambda x: 999 if x == "" else x)
    merged = merged.sort_values(
        ["year_month", "borocode_sort"],
        ascending=[False, True],
    )
    merged = merged.drop(columns=["borocode_sort"])

    # Reorder columns
    merged = merged[["year_month", "borough", "borocode", "sales_index", "rental_index"]]

    # Convert numeric columns to integers where possible
    merged["sales_index"] = merged["sales_index"].apply(
        lambda x: int(x) if pd.notna(x) else ""
    )
    merged["rental_index"] = merged["rental_index"].apply(
        lambda x: int(x) if pd.notna(x) else ""
    )

    # Save to CSV
    output_path = "data/streeteasy_index.csv"
    merged.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
    print(f"Total rows: {len(merged)}")


if __name__ == "__main__":
    main()
