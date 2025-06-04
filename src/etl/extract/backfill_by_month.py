# src/etl/backfill_by_month.py
import argparse
import calendar
from datetime import datetime, timedelta
import logging # Added for logging
import os # Ensure os is imported
import time # Added for delay

from . import download_csv # Relative import for sibling module
from .download_csv import CsvMaxRowsExceededError # Import custom exception
from playwright.sync_api import sync_playwright, TimeoutError # Import TimeoutError

# --- Setup Logger ---
logger = logging.getLogger(__name__)

def get_first_and_last_day_of_month(year: int, month: int) -> tuple[str, str]:
    """Gets the first and last day of a given month and year, in DD-MM-YYYY format."""
    first_day = datetime(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = datetime(year, month, last_day_num)
    return first_day.strftime("%d-%m-%Y"), last_day.strftime("%d-%m-%Y")

def get_weekly_ranges_for_month(year: int, month: int) -> list[tuple[str, str]]:
    """Generates weekly date ranges (Mon-Sun) for a given month and year, in DD-MM-YYYY format."""
    ranges = []
    month_start_date = datetime(year, month, 1)
    _, num_days_in_month = calendar.monthrange(year, month)
    month_end_date = datetime(year, month, num_days_in_month)

    current_start = month_start_date
    while current_start <= month_end_date:
        # Calculate week end: Sunday of the current week, or month end if earlier
        # weekday() returns 0 for Monday, 6 for Sunday
        days_until_sunday = 6 - current_start.weekday()
        current_end = current_start + timedelta(days=days_until_sunday)
        
        # Ensure current_end does not exceed month_end_date
        if current_end > month_end_date:
            current_end = month_end_date
        
        ranges.append((
            current_start.strftime("%d-%m-%Y"), 
            current_end.strftime("%d-%m-%Y")
        ))
        
        # Move to the next day after current_end to start the new week/period
        current_start = current_end + timedelta(days=1)
        # If next start is beyond the month, break
        if current_start.month != month:
            break
            
    return ranges

def get_daily_ranges_for_period(start_date_str: str, end_date_str: str) -> list[tuple[str, str]]:
    """Generates daily date ranges for a given period, in DD-MM-YYYY format."""
    ranges = []
    try:
        current_dt = datetime.strptime(start_date_str, "%d-%m-%Y")
        end_dt = datetime.strptime(end_date_str, "%d-%m-%Y")
    except ValueError:
        # This should ideally not be hit with internal calls using consistent date formats
        logger.error(f"Invalid date format in get_daily_ranges_for_period: start='{start_date_str}', end='{end_date_str}'")
        return []

    while current_dt <= end_dt:
        date_str = current_dt.strftime("%d-%m-%Y")
        ranges.append((date_str, date_str))
        current_dt += timedelta(days=1)
    return ranges

def _download_data_for_period(p, start_d, end_d, output_base, headless=True, max_retries=3, retry_delay=5):
    """Helper function to encapsulate a single download attempt with retries for timeouts."""
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"--- Processing Period: {start_d} to {end_d} (Attempt {attempt + 1}/{max_retries}) ---")
            logger.info(f"Attempting to download to a file based on: {output_base}")
            download_csv.run(
                p,
                start_date=start_d,
                end_date=end_d,
                headless_mode=headless,
                output_filename_base=output_base
            )
            logger.info(f"Successfully processed and downloaded data for period {start_d} to {end_d} into {output_base}.csv")
            return # Success, exit function
        except TimeoutError as te:
            logger.warning(f"TimeoutError during download for period {start_d} to {end_d} (Attempt {attempt + 1}/{max_retries}). Error: {te}")
            attempt += 1
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"All {max_retries} retry attempts failed for period {start_d} to {end_d} due to TimeoutError.")
                raise # Re-raise the TimeoutError to be caught by the caller
        # Keep CsvMaxRowsExceededError and other specific exceptions before the generic Exception
        except CsvMaxRowsExceededError: # This exception should be handled by callers, so re-raise
            raise
        except Exception as e: # Catch other potential exceptions during download
            logger.error(f"An unexpected error occurred during download for {start_d} to {end_d} on attempt {attempt + 1}: {e}")
            # Depending on requirements, you might want to retry on other errors too,
            # or simply raise immediately as done here.
            raise # Re-raise other exceptions immediately

def _process_days_for_week(p, year: int, month: int, week_start_str: str, week_end_str: str, week_part_counter: int, max_retries: int):
    """
    Processes data for each day within a given week if the weekly download failed.
    week_part_counter is the identifier for the week that is being split into days.
    """
    logger.info(f"Splitting week {week_start_str} to {week_end_str} (Month: {year}-{month:02d}, Part: {week_part_counter}) into daily downloads.")
    daily_ranges = get_daily_ranges_for_period(week_start_str, week_end_str)
    for day_start_str, day_end_str in daily_ranges:
        day_part_suffix = datetime.strptime(day_start_str, '%d-%m-%Y').strftime('%d')
        # Filename includes the week's part counter and the specific day
        output_filename_day_base = f"contracts_{year:04d}-{month:02d}-part{week_part_counter}-day{day_part_suffix}"
        try:
            _download_data_for_period(
                p,
                day_start_str,
                day_end_str,
                output_filename_day_base,
                max_retries=max_retries
            )
        except CsvMaxRowsExceededError as e_day:
            logger.error(
                f"Day download ({day_start_str}) for week part {week_part_counter} (Month: {year}-{month:02d}) also failed ({e_day.row_count} > {e_day.limit}). "
                f"Data for this day will be incomplete. File: {e_day.filepath}"
            )
            # Optional: attempt to delete e_day.filepath if it exists and is oversized
        except Exception as e_inner_day:
            logger.error(f"Failed to download data for day {day_start_str} (Week part {week_part_counter}, Month: {year}-{month:02d}). Error: {e_inner_day}")
            logger.warning(f"Skipping day {day_start_str} (Week part {week_part_counter}) for month {year}-{month:02d} due to an unexpected error.")

def _process_week_with_retries(p, year: int, month: int, week_start_str: str, week_end_str: str, part_counter: int, max_retries: int) -> bool:
    """
    Attempts to download data for a single week. If CsvMaxRowsExceededError occurs,
    it delegates to _process_days_for_week.
    Returns True if the week was processed (either successfully downloaded or split into days), False otherwise.
    part_counter is the identifier for this specific week attempt within the month.
    """
    output_filename_week_base = f"contracts_{year:04d}-{month:02d}-part{part_counter}"
    try:
        _download_data_for_period(
            p,
            week_start_str,
            week_end_str,
            output_filename_week_base,
            max_retries=max_retries
        )
        return True # Week downloaded successfully
    except CsvMaxRowsExceededError as e_week:
        logger.warning(
            f"Week part {part_counter} ({week_start_str} to {week_end_str}) for month {year}-{month:02d} failed ({e_week.row_count} > {e_week.limit}). "
            f"Attempting to split by days. Original weekly file: {e_week.filepath}"
        )
        if os.path.exists(e_week.filepath):
            try:
                os.remove(e_week.filepath)
                logger.info(f"Deleted oversized weekly file: {e_week.filepath}")
            except OSError as oe:
                logger.error(f"Error deleting oversized weekly file {e_week.filepath}: {oe}")
        
        _process_days_for_week(p, year, month, week_start_str, week_end_str, part_counter, max_retries=max_retries)
        return True # Week processing attempted by splitting into days
    except Exception as e_inner_week:
        logger.error(f"Failed to download data for week part {part_counter} ({week_start_str} - {week_end_str}) of month {year}-{month:02d}. Error: {e_inner_week}")
        logger.warning(f"Skipping week part {part_counter} for month {year}-{month:02d} due to an unexpected error.")
        return False # Week processing failed

def _process_month_with_retries(p, year: int, month: int, max_retries: int):
    """
    Processes data for a single month.
    Attempts to download the whole month first. If that fails due to CsvMaxRowsExceededError,
    it iterates through each week of the month, calling _process_week_with_retries.
    """
    month_start_date_str, month_end_date_str = get_first_and_last_day_of_month(year, month)
    output_filename_month_base = f"contracts_{year:04d}-{month:02d}"

    logger.info(f"--- Processing Month: {year}-{month:02d} ({month_start_date_str} to {month_end_date_str}) ---")
    logger.info(f"Attempting to download full month to: {output_filename_month_base}")

    try:
        _download_data_for_period(
            p,
            month_start_date_str,
            month_end_date_str,
            output_filename_month_base,
            max_retries=max_retries
        )
        logger.info(f"Successfully downloaded full month {year}-{month:02d}.")
    except CsvMaxRowsExceededError as e:
        logger.warning(
            f"Month {year}-{month:02d} ({month_start_date_str} to {month_end_date_str}) failed due to too many rows ({e.row_count} > {e.limit}). "
            f"Attempting to split by weeks. Original monthly file: {e.filepath}"
        )
        if os.path.exists(e.filepath):
            try:
                os.remove(e.filepath)
                logger.info(f"Deleted oversized monthly file: {e.filepath}")
            except OSError as oe:
                logger.error(f"Error deleting oversized monthly file {e.filepath}: {oe}")

        weekly_ranges = get_weekly_ranges_for_month(year, month)
        part_counter = 0  # This counter is for parts of the month (i.e., weeks or failed weeks split into days)
        
        for week_start_str, week_end_str in weekly_ranges:
            if _process_week_with_retries(p, year, month, week_start_str, week_end_str, part_counter, max_retries=max_retries):
                part_counter += 1 # Increment if week processing was attempted (success or day split)
            else:
                # If _process_week_with_retries returns False, it means an unexpected error occurred for that week,
                # and it was skipped. We still increment part_counter to avoid filename collisions for subsequent weeks.
                part_counter += 1 
                logger.warning(f"Week from {week_start_str} to {week_end_str} (part {part_counter-1}) for month {year}-{month:02d} was skipped due to an unrecoverable error during its processing.")

    except Exception as e_month: # Catch other exceptions for the whole month attempt
        logger.error(f"An unexpected error occurred processing month {year}-{month:02d}. Error: {e_month}")
        logger.warning(f"Skipping month {year}-{month:02d} due to this error.")

def run_backfill(global_start_date_str: str, global_end_date_str: str, delay_seconds: int = 0, max_retries: int = 3):
    """
    Downloads contract data month by month for the specified global date range.
    If a month fails due to CsvMaxRowsExceededError, it retries by splitting the month into weeks.
    Dates are expected in YYYY-MM-DD format for global range.
    """
    try:
        current_date = datetime.strptime(global_start_date_str, "%Y-%m-%d")
        global_end_date = datetime.strptime(global_end_date_str, "%Y-%m-%d")
    except ValueError:
        logger.error("Invalid global start or end date format. Please use YYYY-MM-DD.")
        return

    if current_date > global_end_date:
        logger.error("Global start date cannot be after global end date.")
        return

    with sync_playwright() as playwright:
        while current_date <= global_end_date:
            year = current_date.year
            month = current_date.month
            
            try:
                _process_month_with_retries(playwright, year, month, max_retries=max_retries)
            except TimeoutError: # Catch TimeoutError if it propagates from _download_data_for_period
                logger.error(f"Backfill process failed for month {year}-{month:02d} after multiple retries due to TimeoutError. Stopping backfill.")
                break # Stop the backfill process
            except Exception as e_run: # Catch any other unexpected error from _process_month_with_retries
                logger.error(f"Backfill process encountered an unrecoverable error for month {year}-{month:02d}: {e_run}. Stopping backfill.")
                break # Stop the backfill process

            # Move to the first day of the next month
            if month == 12:
                current_date = datetime(year + 1, 1, 1)
            else:
                current_date = datetime(year, month + 1, 1)
            
            logger.info("-" * 40)

            if delay_seconds > 0:
                logger.info(f"Waiting for {delay_seconds} seconds before next download.")
                time.sleep(delay_seconds)

    logger.info("Backfill process completed.")

def main():
    parser = argparse.ArgumentParser(description="Backfill contract data by downloading it month by month.")
    parser.add_argument("global_start_date", help="Global start date for backfill (format: YYYY-MM-DD)")
    parser.add_argument("global_end_date", help="Global end date for backfill (format: YYYY-MM-DD)")
    parser.add_argument("--delay", type=int, default=0, help="Optional delay in seconds between download attempts (default: 0)")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries for a download period if a timeout occurs (default: 3)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose (DEBUG level) logging")
    
    args = parser.parse_args()

    # --- Configure Logging ---
    log_level = logging.DEBUG if args.verbose else logging.INFO
    # Configure root logger if download_csv doesn't configure its own and we want its logs too
    # Or configure only this script's logger: logging.getLogger(__name__).setLevel(log_level)
    # For simplicity, basicConfig will affect the root logger and propagate to download_csv if it uses getLogger.
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info(f"Starting backfill from {args.global_start_date} to {args.global_end_date} with {args.retries} retries per period.")
    run_backfill(args.global_start_date, args.global_end_date, args.delay, args.retries)

if __name__ == "__main__":
    main() 