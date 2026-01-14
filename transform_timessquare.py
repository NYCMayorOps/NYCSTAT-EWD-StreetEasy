import re
import sys
import json
import requests

# Data source URL
INFOGRAM_URL = "https://e.infogram.com/4f23de5e-61de-4702-96f8-ab86d5e8bb2b"

# Month name to number mapping
MONTH_MAP = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12",
}


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
    """Transform wide table to long format with YYYYMM month column."""
    # Extract years from header row
    years = [cell["value"] for cell in table[0][1:]]

    rows = []
    for row in table[1:]:
        month_name = row[0]["value"]
        month_num = MONTH_MAP.get(month_name)
        if not month_num:
            continue

        for i, year in enumerate(years):
            if i + 1 < len(row):
                value = row[i + 1]["value"].strip().replace(",", "").replace(" ", "")
                if value:
                    rows.append((f"{year}{month_num}", int(value)))

    # Sort by month descending
    rows.sort(key=lambda x: x[0], reverse=True)
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
        f.write("Month,Count\n")
        for month, count in rows:
            f.write(f"{month},{count}\n")

    print(f"Saved to {output_path}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()
