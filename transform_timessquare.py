import re
import sys
import json
import requests

# Data source URL
INFOGRAM_URL = "https://e.infogram.com/4f23de5e-61de-4702-96f8-ab86d5e8bb2b"

# Month name to number mapping
MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

# Baseline values (April 2019 - March 2020)
# Months 4-12 use 2019 values, months 1-3 use 2020 values
BASELINE = {
    1: 9403463,    # January 2020
    2: 9599746,    # February 2020
    3: 302374,     # March 2020
    4: 11256708,   # April 2019
    5: 11642886,   # May 2019
    6: 11836655,   # June 2019
    7: 12515144,   # July 2019
    8: 12529524,   # August 2019
    9: 11334376,   # September 2019
    10: 11367532,  # October 2019
    11: 10135928,  # November 2019
    12: 10559750,  # December 2019
}

# Fixed SPID value
SPID = 35


def download_and_parse(url, retries=3, timeout=30):
    """Download Infogram page and extract embedded data."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            else:
                print(f"Failed to download {url} after {retries} attempts: {e}")
                sys.exit(1)

    # Extract infographicData JSON from page
    match = re.search(r"window\.infographicData\s*=\s*({.*?});", response.text, re.DOTALL)
    if not match:
        print("Could not find infographicData in page")
        sys.exit(1)

    return json.loads(match.group(1))


def extract_chart_data(data):
    """Navigate the Infogram data structure to find chart data."""
    entities = data["elements"]["content"]["content"]["entities"]

    # Find the chart entity
    for entity_id, entity in entities.items():
        if entity.get("type") == "RESPONSIVE_CHART" and "data" in entity:
            return entity["data"][0]

    print("Could not find chart data in entities")
    sys.exit(1)


def transform_to_long(table):
    """Transform wide table to new format with 5 columns."""
    # Extract years from header row
    years = [int(cell["value"]) for cell in table[0][1:]]

    rows = []
    for row in table[1:]:
        month_name = row[0]["value"]
        month_num = MONTH_MAP.get(month_name)
        if not month_num:
            continue

        for i, year in enumerate(years):
            if i + 1 < len(row):
                value_str = row[i + 1]["value"].strip().replace(",", "").replace(" ", "")
                if value_str:
                    value = int(value_str)
                    # Format: M/1/YYYY
                    date_str = f"{month_num}/1/{year}"
                    baseline = BASELINE.get(month_num, 0)
                    # Calculate percent change: Value / PseudoBaseline
                    pct_chg = round(value / baseline, 4) if baseline else ""
                    rows.append((year, month_num, date_str, value, baseline, pct_chg))

    # Sort by year desc, then month desc
    rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return rows


def main():
    print("Downloading Times Square pedestrian data...")
    data = download_and_parse(INFOGRAM_URL)

    print("Extracting chart data...")
    table = extract_chart_data(data)

    print("Transforming data...")
    rows = transform_to_long(table)

    # Save to CSV
    output_path = "data/timessquare_pedestrian.csv"
    with open(output_path, "w") as f:
        f.write("date.1,Value,SPID,PseudoBaseline,Baseline Perc Chg\n")
        for year, month_num, date_str, value, baseline, pct_chg in rows:
            f.write(f"{date_str},{value},{SPID},{baseline},{pct_chg}\n")

    print(f"Saved to {output_path}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()
