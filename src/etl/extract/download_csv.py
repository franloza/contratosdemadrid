from playwright.sync_api import Playwright, sync_playwright, expect
import os # Added for joining paths
import re # Added for regex
import operator # Added for operations
import argparse # Added for CLI arguments
from datetime import datetime # Added for date validation/formatting if needed
import csv # Added for CSV row count validation
import logging
from src.etl.config import DATA_DIR # Import DATA_DIR from new location

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Custom Exception for CSV Row Limit --- # Added by AI
class CsvMaxRowsExceededError(Exception):
    """Custom exception raised when the CSV row count exceeds the defined limit."""
    def __init__(self, message, filepath, row_count, limit):
        super().__init__(message)
        self.filepath = filepath
        self.row_count = row_count
        self.limit = limit
        self.message = message # Store message explicitly for easier access if needed

    def __str__(self):
        return f"{self.message} (File: {self.filepath}, Rows: {self.row_count}, Limit: {self.limit})"

# --- Helper function to solve arithmetic CAPTCHA ---
def solve_arithmetic_captcha(page) -> str | None:
    logger.debug("Attempting to solve arithmetic CAPTCHA...")
    question_text = None
    
    captcha_css_selector = "#pcon-contratos-menores-export-results-form > div.captcha > div > span"

    try:
        captcha_element_locator = page.locator(captcha_css_selector)
        expect(captcha_element_locator).to_be_visible(timeout=8000) # Reduced timeout

        if captcha_element_locator.count() == 1:
            question_text = captcha_element_locator.first.text_content()
            if question_text:
                question_text = question_text.strip()
                logger.debug(f'Found CAPTCHA question using provided CSS selector: "{question_text}"')
            else:
                 logger.debug(f"CAPTCHA element found with CSS selector '{captcha_css_selector}' but it has no text content.")
        elif captcha_element_locator.count() > 1:
            logger.debug(f"Warning: Multiple elements ({captcha_element_locator.count()}) found for CAPTCHA selector '{captcha_css_selector}'. Using the first visible one.")
            for i in range(captcha_element_locator.count()):
                elem = captcha_element_locator.nth(i)
                if elem.is_visible():
                    question_text = elem.text_content()
                    if question_text:
                        question_text = question_text.strip()
                        logger.debug(f'Found CAPTCHA question (from multiple, using first visible): "{question_text}"')
                        break
        else:
            logger.debug(f"CAPTCHA element not found or not visible with selector: '{captcha_css_selector}' after waiting.")
            return None

    except Exception as e:
        logger.debug(f"Error while trying to find/verify CAPTCHA question text with selector '{captcha_css_selector}': {e}")
        return None

    if not question_text:
        logger.debug("Could not reliably find CAPTCHA question text on the page using provided selector.")
        return None

    match = re.search(r'^\s*(\d+)\s*([+\-*×])\s*(\d+)\s*=?\s*$', question_text)
    
    if match:
        num1_str, op_str, num2_str = match.groups()
        num1 = int(num1_str)
        num2 = int(num2_str)
        
        ops = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "x": operator.mul 
        }
        
        if op_str in ops:
            result = ops[op_str](num1, num2)
            logger.debug(f"Solved CAPTCHA: {num1} {op_str} {num2} = {result}")
            return str(result)
        else:
            logger.debug(f"Unknown operator: '{op_str}'")
            return None
    else:
        logger.debug(f'Could not parse arithmetic question from identified text: "{question_text}". Regex did not match.')
        return None

def add_csv_row_numbers(input_path, output_path, col_name="row_number", encoding='utf-8-sig'):
    """Adds a 'row_number' column to the beginning of a CSV file."""
    with open(input_path, 'r', newline='', encoding=encoding) as infile, \
         open(output_path, 'w', newline='', encoding=encoding) as outfile:
        
        reader = csv.reader(infile, delimiter=';')
        writer = csv.writer(outfile, delimiter=';')
        
        try:
            header = next(reader)
            writer.writerow([col_name] + header) # Write new header
        except StopIteration: # Handles empty CSV
            writer.writerow([col_name]) # Write just the new header if CSV was empty or header-only
            return

        for i, row in enumerate(reader, 1): # Number data rows starting from 1
            writer.writerow([i] + row)

def run(playwright: Playwright, start_date: str, end_date: str, headless_mode: bool, output_filename_base: str | None = None, enable_screenshots: bool = False, should_add_row_numbers: bool = True) -> str:
    browser = None
    context = None
    page = None # Initialize page to None for the finally block
    final_download_path = None # Initialize final_download_path
    try:
        browser = playwright.chromium.launch(headless=headless_mode) 
        context = browser.new_context(accept_downloads=True) 
        page = context.new_page()

        # Construct the URL dynamically
        base_url = "https://contratos-publicos.comunidad.madrid/contratos"
        params = f"tipo_publicacion=All&createddate={start_date}&createddate_1={end_date}&ss_buscador_estado_situacion=4&f%5B0%5D=tipo_publicacion=All"
        target_url = f"{base_url}?{params}"
        logger.info(f"Navigating to: {target_url}")

        page.goto(target_url)
        logger.debug("Navigated to the initial page.")

        page.get_by_role("link", name="Exportar CSV").click()
        logger.debug("Clicked 'Exportar CSV' link.")
        
        captcha_form_selector = "#pcon-contratos-menores-export-results-form"
        expect(page.locator(captcha_form_selector)).to_be_visible(timeout=12000) # Reduced timeout
        
        captcha_input_selector = 'input[name="captcha_response"]'
        expect(page.locator(captcha_input_selector)).to_be_visible(timeout=8000) # Reduced timeout
        
        captcha_solution = solve_arithmetic_captcha(page)
        
        if captcha_solution:
            captcha_textbox = page.locator(captcha_input_selector)
            expect(captcha_textbox).to_be_visible(timeout=5000)
            expect(captcha_textbox).to_be_enabled(timeout=5000)
            captcha_textbox.fill(captcha_solution)
            logger.debug(f"Filled CAPTCHA with calculated solution: {captcha_solution}")
        else:
            logger.error("Could not solve CAPTCHA automatically.")
            if page and enable_screenshots:
                page.screenshot(path="captcha_solve_failure.png")
                logger.debug("Screenshot captured as captcha_solve_failure.png")
            raise Exception("Failed to solve CAPTCHA automatically.")

        page.wait_for_timeout(250) # Reduced timeout
        page.get_by_role("button", name="Exportar").click()
        logger.debug("Clicked 'Exportar' button.")
        
        logger.debug("Waiting for 'Descargar CSV' button using role-based selector...")
        download_button_locator = page.get_by_role("button", name="Descargar CSV")
        expect(download_button_locator).to_be_visible(timeout=8000) # Reduced timeout

        page.wait_for_timeout(250) # Reduced timeout 

        with page.expect_download(timeout=30000) as download_info: 
            download_button_locator.click() 
            logger.debug("Clicked 'Descargar CSV' button. Waiting for download...")
        
        download = download_info.value
        suggested_filename_on_server = download.suggested_filename
        logger.debug(f"Download started (server suggested filename: {suggested_filename_on_server})")
        
        # Construct download_path earlier to ensure it's available for cleanup if download fails before save_as
        # However, suggested_filename is only known after download starts.
        # We'll define it here before save_as.
        # data_dir = "data" # Old hardcoded path
        os.makedirs(DATA_DIR, exist_ok=True) # Ensure DATA_DIR directory exists

        if output_filename_base:
            # Ensure it ends with .csv
            if not output_filename_base.lower().endswith('.csv'):
                final_filename = f"{output_filename_base}.csv"
            else:
                final_filename = output_filename_base
        else:
            # Fallback for direct CLI use or if no name is provided
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(suggested_filename_on_server)
            # Ensure ext is .csv, if not, use .csv
            ext = ext if ext.lower() == '.csv' else '.csv'
            final_filename = f"{base}_{timestamp}{ext}"
            if final_filename == f"_{timestamp}.csv": # if suggested was empty or just extension
                 final_filename = f"download_{timestamp}.csv"

        final_download_path = os.path.join(DATA_DIR, final_filename)
         
        download.save_as(final_download_path)
        logger.debug(f"File saved to: {final_download_path}")

        original_csv_error = None # Variable to store the error if it occurs

        # --- CSV Row Count Validation ---
        MAX_ROWS_LIMIT = 50000
        row_count = 0
        try:
            with open(final_download_path, mode='r', encoding='utf-8-sig') as csvfile: # utf-8-sig to handle potential BOM
                reader = csv.reader(csvfile)
                # Count rows by iterating (more memory efficient than list(reader) for huge files)
                for row in reader:
                    row_count += 1
            
            logger.debug(f"Downloaded CSV contains {row_count} rows.")

            if row_count > MAX_ROWS_LIMIT:
                error_message = (
                    f"The downloaded CSV file '{final_download_path}' contains {row_count} rows (limit is {MAX_ROWS_LIMIT}). "
                    f"This indicates the export limit may have been reached, and the data could be incomplete."
                )
                logger.error(error_message)
                # Store the error instead of raising immediately
                original_csv_error = CsvMaxRowsExceededError(error_message, final_download_path, row_count, MAX_ROWS_LIMIT)
            elif row_count == 0:
                 logger.warning(f"The downloaded CSV file '{final_download_path}' contains 0 rows. This might be expected or indicate no data for the period.")
            else: # Only log success if no error and not empty
                logger.debug(f"CSV validation successful. File '{final_download_path}' does not appear to hit the row limit.")

        except FileNotFoundError:
            logger.error(f"Downloaded file not found at {final_download_path} for row count validation.")
            raise # Re-raise the error as this is unexpected if save_as succeeded
        except Exception as e:
            logger.error(f"Error during CSV row count validation: {e}")
            raise # Re-raise other CSV processing errors
        
        # --- Add Row Numbers (if enabled) ---
        # This block will now execute even if original_csv_error is set,
        # unless a FileNotFoundError or other Exception occurred in the CSV validation block and was re-raised.
        if should_add_row_numbers:
            logger.info(f"Adding row numbers to '{final_download_path}'...")
            temp_numbered_path = final_download_path + ".tmp_numbered"
            try:
                add_csv_row_numbers(final_download_path, temp_numbered_path, encoding='utf-8-sig')
                os.replace(temp_numbered_path, final_download_path)
                logger.info(f"Successfully added row numbers. Updated file: '{final_download_path}'")
            except Exception as e_row_add:
                logger.error(f"Error adding row numbers to '{final_download_path}': {e_row_add}")
                if os.path.exists(temp_numbered_path):
                    try:
                        os.remove(temp_numbered_path)
                        logger.debug(f"Cleaned up temporary file: {temp_numbered_path}")
                    except OSError as e_remove:
                        logger.error(f"Could not remove temporary file {temp_numbered_path}: {e_remove}")
                # If adding row numbers fails, this new exception should take precedence.
                # The original CsvMaxRowsExceededError (if any) will not be raised if this path is taken.
                raise Exception(f"Failed to add row numbers to the CSV. Original error: {e_row_add}")

        # --- Re-raise CsvMaxRowsExceededError if it occurred ---
        if original_csv_error:
            raise original_csv_error # Propagate the original error after attempting to add row numbers

        return final_download_path # Return the path of the downloaded file

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        try:
            if page and enable_screenshots:
                screenshot_path = "error_screenshot.png"
                page.screenshot(path=screenshot_path)
                logger.debug(f"Screenshot saved to {screenshot_path} on error.")
        except Exception as se:
            logger.error(f"Could not save screenshot: {se}")
        raise # Re-raise the exception so it can be caught by the caller
    finally:
        logger.debug("Closing browser.")
        if context:
            context.close()
        if browser:
            browser.close()

def main():
    parser = argparse.ArgumentParser(description="Download CSV from Comunidad de Madrid contracts portal with specified date range.")
    parser.add_argument("start_date", help="Start date for the contracts search (format: DD-MM-YYYY)")
    parser.add_argument("end_date", help="End date for the contracts search (format: DD-MM-YYYY)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (no UI)")
    parser.add_argument("--output-name", help="Optional base name for the output CSV file (e.g., 'my_contracts'). Extension .csv will be added. If not provided, a timestamped name based on server suggestion will be used.")
    parser.add_argument(
        "--skip-row-numbers",
        action="store_true",
        help="Skip adding row numbers to the CSV (default: row numbers are added)."
    )

    args = parser.parse_args()

    # Basic date format validation (dd-mm-yyyy)
    date_format_regex = r"^\d{2}-\d{2}-\d{4}$"
    if not re.match(date_format_regex, args.start_date):
        print(f"Error: Start date '{args.start_date}' is not in DD-MM-YYYY format.")
        return
    if not re.match(date_format_regex, args.end_date):
        print(f"Error: End date '{args.end_date}' is not in DD-MM-YYYY format.")
        return
    
    # Check if start_date and end_date are the same
    if args.start_date == args.end_date:
        print(f"Error: Start date ('{args.start_date}') and end date ('{args.end_date}') cannot be the same. Please provide a date range.")
        # Suggesting how to get a single day if that's the intent might be tricky without knowing server logic.
        # For now, just enforce they are different.
        return

    # More sophisticated date validation (e.g., start_date <= end_date)
    try:
        start_dt_obj = datetime.strptime(args.start_date, "%d-%m-%Y")
        end_dt_obj = datetime.strptime(args.end_date, "%d-%m-%Y")
        if start_dt_obj > end_dt_obj:
            print(f"Error: Start date '{args.start_date}' cannot be after end date '{args.end_date}'.")
            return
    except ValueError:
        # This should ideally be caught by the regex, but as a safeguard for date validity:
        print("Error: Invalid date provided (could not parse, e.g., 31-02-2024 is not a valid date).")
        return

    add_numbers_flag = not args.skip_row_numbers

    with sync_playwright() as playwright:
        try:
            downloaded_file = run(
                playwright, 
                args.start_date, 
                args.end_date, 
                args.headless, 
                args.output_name,
                # enable_screenshots is not set from CLI in this main, so it will use its default from 'run' signature
                should_add_row_numbers=add_numbers_flag
            )
            print(f"Script completed successfully. File available at: {downloaded_file}")
        except Exception as e:
            print(f"Script execution failed: {e}")


if __name__ == "__main__":
    main()
