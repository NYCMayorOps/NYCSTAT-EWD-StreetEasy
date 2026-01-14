# NYCSTAT-EWD-StreetEasy

Automated data pipeline for NYC Economic & Workforce Development indicators. Downloads, transforms, and publishes data daily via GitHub Actions.

## Data Sources

| Dataset | Source | Update Frequency |
|---------|--------|------------------|
| StreetEasy Rental & Sales Index | [StreetEasy](https://streeteasy.com/) | Monthly |
| Times Square Pedestrian Count | [Times Square Alliance](https://www.timessquarenyc.org/) | Monthly |

## Output Files

### 1. StreetEasy Index (`data/streeteasy_index.csv`)

NYC rental and sales price indices by borough.

| Column | Description |
|--------|-------------|
| year_month | Month (YYYY-MM) |
| borough | Borough code (MN, BK, QN, NYC) |
| borocode | Borough number (1=Manhattan, 3=Brooklyn, 4=Queens) |
| sales_index | StreetEasy sales price index |
| rental_index | StreetEasy rental price index |

**Raw URL:**
```
https://raw.githubusercontent.com/NYCMayorOps/NYCSTAT-EWD-StreetEasy/main/data/streeteasy_index.csv
```

### 2. Times Square Pedestrian Count (`data/timessquare_pedestrian.csv`)

Daily average pedestrian counts in Times Square.

| Column | Description |
|--------|-------------|
| date.1 | First day of month (M/1/YYYY) |
| Value | Average daily pedestrian count |
| SPID | Indicator ID (35) |
| PseudoBaseline | Baseline value from same month in Apr 2019 - Mar 2020 |
| Baseline Perc Chg | Value / PseudoBaseline |

**Raw URL:**
```
https://raw.githubusercontent.com/NYCMayorOps/NYCSTAT-EWD-StreetEasy/main/data/timessquare_pedestrian.csv
```

## Automation

GitHub Actions runs daily at 6:00 AM UTC:
1. Downloads latest data from sources
2. Transforms to standardized format
3. Commits changes (if data updated)

Manual trigger available via GitHub Actions tab.

## Usage in Power BI

**StreetEasy:**
```powerquery
let
    Source = Csv.Document(
        Web.Contents("https://raw.githubusercontent.com/NYCMayorOps/NYCSTAT-EWD-StreetEasy/main/data/streeteasy_index.csv"),
        [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"year_month", type date},
        {"borough", type text},
        {"borocode", Int64.Type},
        {"sales_index", Int64.Type},
        {"rental_index", Int64.Type}
    })
in
    #"Changed Type"
```

**Times Square:**
```powerquery
let
    Source = Csv.Document(
        Web.Contents("https://raw.githubusercontent.com/NYCMayorOps/NYCSTAT-EWD-StreetEasy/main/data/timessquare_pedestrian.csv"),
        [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"date.1", type date},
        {"Value", Int64.Type},
        {"SPID", Int64.Type},
        {"PseudoBaseline", type number},
        {"Baseline Perc Chg", type number}
    })
in
    #"Changed Type"
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run transformations
python transform.py              # StreetEasy
python transform_timessquare.py  # Times Square
```

## Files

```
├── .github/workflows/
│   └── daily-refresh.yml      # GitHub Actions workflow
├── data/
│   ├── streeteasy_index.csv   # StreetEasy output
│   └── timessquare_pedestrian.csv  # Times Square output
├── transform.py               # StreetEasy ETL script
├── transform_timessquare.py   # Times Square ETL script
├── requirements.txt           # Python dependencies
└── README.md
```
