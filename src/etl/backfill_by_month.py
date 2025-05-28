# src/etl/backfill_by_month.py
import argparse
import calendar
from datetime import datetime, timedelta
import time
import os

# We will import the run function from download_csv
# Assuming download_csv.py is in the same directory or PYTHONPATH is set up
from . import download_csv # Relative import for sibling module
from playwright.sync_api import sync_playwright

def get_first_and_last_day_of_month(year: int, month: int) -> tuple[str, str]:
    """Gets the first and last day of a given month and year, in DD-MM-YYYY format."""
    first_day = datetime(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = datetime(year, month, last_day_num)
    return first_day.strftime("%d-%m-%Y"), last_day.strftime("%d-%m-%Y")

def run_backfill(global_start_date_str: str, global_end_date_str: str):
    """
    Downloads contract data month by month for the specified global date range.
    Dates are expected in YYYY-MM-DD format for global range.
    """
    try:
        current_date = datetime.strptime(global_start_date_str, "%Y-%m-%d")
        global_end_date = datetime.strptime(global_end_date_str, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid global start or end date format. Please use YYYY-MM-DD.")
        return

    if current_date > global_end_date:
        print("Error: Global start date cannot be after global end date.")
        return

    with sync_playwright() as playwright:
        while current_date <= global_end_date:
            year = current_date.year
            month = current_date.month
            
            month_start_date_str, month_end_date_str = get_first_and_last_day_of_month(year, month)
            
            # Create a specific output filename for this month
            # e.g., contracts_2023-01.csv
            output_filename = f"contracts_{year:04d}-{month:02d}" # .csv will be added by download_csv.run

            print(f"--- Processing: {month_start_date_str} to {month_end_date_str} ---")
            print(f"Attempting to download to a file based on: {output_filename}")

            try:
                download_csv.run(
                    playwright,
                    start_date=month_start_date_str,
                    end_date=month_end_date_str,
                    headless_mode=True, # Backfill always runs headless
                    output_filename_base=output_filename
                )
                print(f"Successfully processed and downloaded data for {year}-{month:02d}.")
            except Exception as e:
                print(f"Failed to download data for {month_start_date_str} - {month_end_date_str}. Error: {e}")
                print(f"Skipping to next month due to error.")
            
            # Move to the first day of the next month
            if month == 12:
                current_date = datetime(year + 1, 1, 1)
            else:
                current_date = datetime(year, month + 1, 1)
            
            print("-" * 40)

    print("Backfill process completed.")

def main():
    parser = argparse.ArgumentParser(description="Backfill contract data by downloading it month by month.")
    parser.add_argument("global_start_date", help="Global start date for backfill (format: YYYY-MM-DD)")
    parser.add_argument("global_end_date", help="Global end date for backfill (format: YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    run_backfill(args.global_start_date, args.global_end_date)

if __name__ == "__main__":
    main() 