# Contratos de Madrid

This project provides scripts to download contract data from the Comunidad de Madrid public contracts portal.

## Features

- Download contract data as CSV files for specified date ranges.
- Automated CAPTCHA solving for the download process.
- CLI for specifying date ranges and headless browser operation for the underlying download script.
- Row count validation to detect incomplete CSV exports (max 50,000 rows).
- Monthly backfill script to download data in monthly chunks, generating uniquely named files (e.g., `data/contracts_YYYY-MM.csv`).
- Managed Python environment and script execution via `uv` and `Makefile`.

## Prerequisites

- Python 3.11+ (as specified in `pyproject.toml`)
- `uv` (Python package installer and virtual environment manager from Astral): [Installation Guide](https://github.com/astral-sh/uv)
- `make` (for using the Makefile shortcuts)

## Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repository-url>
    cd contratosdemadrid
    ```

2.  **Install dependencies and set up the environment using `uv` and `make`:**
    This command will create a virtual environment (usually in `.venv`), install Python packages specified in `pyproject.toml`, and download necessary Playwright browser binaries.
    ```bash
    make install
    ```

## Running the Scripts

Make sure your virtual environment is active if you are not using `make` targets directly (e.g., `source .venv/bin/activate`). However, the `make` targets are designed to run commands within the `uv` managed environment.

### Backfill Data by Month

This script iterates month by month for the given global date range and downloads a separate CSV for each month into the `data/` directory. Dates must be in `YYYY-MM-DD` format.

```bash
make backfill START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD
```

**Example:**
```bash
make backfill START_DATE=2023-01-01 END_DATE=2023-03-31
```
This script always runs in headless mode by calling the underlying download script headlessly.

If you need to download data for a specific, one-off date range (not as part of a monthly backfill), you can still run the `download_csv.py` script directly using `uv run`. Remember to activate your environment (`source .venv/bin/activate`) or prefix with `uv run -- `.

**Example of direct execution for a specific range:**
```bash
# Ensure your venv is active or use uv run
# source .venv/bin/activate 
# python src/etl/download_csv.py 01-01-2024 05-01-2024 --headless --output-name my_specific_download

# Or with uv run directly (from project root):
uv run -- python src/etl/download_csv.py 01-01-2024 05-01-2024 --headless --output-name specific_contracts_jan_1_to_5
```
This will save `specific_contracts_jan_1_to_5.csv` in the `data/` directory.

## Project Structure

- `src/etl/download_csv.py`: Script for downloading data for a specific date range. Can be run directly for one-off downloads.
- `src/etl/backfill_by_month.py`: Script for backfilling data in monthly chunks. This is the primary script for bulk downloads via `make backfill`.
- `Makefile`: Contains helper commands for setup and running the backfill script.
- `pyproject.toml`: Project metadata and dependencies for `uv`.
- `uv.lock`: Lock file for reproducible dependency installations with `uv`.
- `data/`: Default directory where downloaded CSV files are saved (created automatically).
