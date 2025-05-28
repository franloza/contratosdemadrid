from playwright.sync_api import Playwright, sync_playwright, expect
import os # Added for joining paths
import re # Added for regex
import operator # Added for operations
import argparse # Added for CLI arguments
from datetime import datetime # Added for date validation/formatting if needed
import csv # Added for CSV row count validation

# --- Helper function to solve arithmetic CAPTCHA ---
def solve_arithmetic_captcha(page) -> str | None:
    print("Attempting to solve arithmetic CAPTCHA...")
    question_text = None
    
    captcha_css_selector = "#pcon-contratos-menores-export-results-form > div.captcha > div > span"

    try:
        captcha_element_locator = page.locator(captcha_css_selector)
        expect(captcha_element_locator).to_be_visible(timeout=8000) # Reduced timeout

        if captcha_element_locator.count() == 1:
            question_text = captcha_element_locator.first.text_content()
            if question_text:
                question_text = question_text.strip()
                print(f'Found CAPTCHA question using provided CSS selector: "{question_text}"')
            else:
                 print(f"CAPTCHA element found with CSS selector '{captcha_css_selector}' but it has no text content.")
        elif captcha_element_locator.count() > 1:
            print(f"Warning: Multiple elements ({captcha_element_locator.count()}) found for CAPTCHA selector '{captcha_css_selector}'. Using the first visible one.")
            for i in range(captcha_element_locator.count()):
                elem = captcha_element_locator.nth(i)
                if elem.is_visible():
                    question_text = elem.text_content()
                    if question_text:
                        question_text = question_text.strip()
                        print(f'Found CAPTCHA question (from multiple, using first visible): "{question_text}"')
                        break
        else:
            print(f"CAPTCHA element not found or not visible with selector: '{captcha_css_selector}' after waiting.")
            return None

    except Exception as e:
        print(f"Error while trying to find/verify CAPTCHA question text with selector '{captcha_css_selector}': {e}")
        return None

    if not question_text:
        print("Could not reliably find CAPTCHA question text on the page using provided selector.")
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
            print(f"Solved CAPTCHA: {num1} {op_str} {num2} = {result}")
            return str(result)
        else:
            print(f"Unknown operator: '{op_str}'")
            return None
    else:
        print(f'Could not parse arithmetic question from identified text: "{question_text}". Regex did not match.')
        return None

def run(playwright: Playwright, start_date: str, end_date: str, headless_mode: bool, output_filename_base: str | None = None) -> str:
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
        print(f"Navigating to: {target_url}")

        page.goto(target_url)
        print("Navigated to the initial page.")

        page.get_by_role("link", name="Exportar CSV").click()
        print("Clicked 'Exportar CSV' link.")
        
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
            print(f"Filled CAPTCHA with calculated solution: {captcha_solution}")
        else:
            print("Could not solve CAPTCHA automatically.")
            if page:
                page.screenshot(path="captcha_solve_failure.png")
                print("Screenshot captured as captcha_solve_failure.png")
            raise Exception("Failed to solve CAPTCHA automatically.")

        page.wait_for_timeout(250) # Reduced timeout
        page.get_by_role("button", name="Exportar").click()
        print("Clicked 'Exportar' button.")
        
        print("Waiting for 'Descargar CSV' button using role-based selector...")
        download_button_locator = page.get_by_role("button", name="Descargar CSV")
        expect(download_button_locator).to_be_visible(timeout=8000) # Reduced timeout

        page.wait_for_timeout(250) # Reduced timeout 

        with page.expect_download(timeout=30000) as download_info: 
            download_button_locator.click() 
            print("Clicked 'Descargar CSV' button. Waiting for download...")
        
        download = download_info.value
        suggested_filename_on_server = download.suggested_filename
        print(f"Download started (server suggested filename: {suggested_filename_on_server})")
        
        # Construct download_path earlier to ensure it's available for cleanup if download fails before save_as
        # However, suggested_filename is only known after download starts.
        # We'll define it here before save_as.
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True) # Ensure 'data' directory exists

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

        final_download_path = os.path.join(data_dir, final_filename)
         
        download.save_as(final_download_path)
        print(f"File saved to: {final_download_path}")

        # --- CSV Row Count Validation ---
        MAX_ROWS_LIMIT = 50000
        row_count = 0
        try:
            with open(final_download_path, mode='r', encoding='utf-8-sig') as csvfile: # utf-8-sig to handle potential BOM
                reader = csv.reader(csvfile)
                # Count rows by iterating (more memory efficient than list(reader) for huge files)
                for row in reader:
                    row_count += 1
            
            print(f"Downloaded CSV contains {row_count} rows.")

            if row_count > MAX_ROWS_LIMIT:
                error_message = (
                    f"Error: The downloaded CSV file '{final_download_path}' contains exactly {MAX_ROWS_LIMIT} rows. "
                    f"This indicates the export limit may have been reached, and the data could be incomplete. "
                    f"Please refine the search criteria (e.g., use a smaller date range) and try again."
                )
                print(error_message)
                # Optionally, delete the potentially incomplete file
                # os.remove(final_download_path)
                # print(f"Deleted potentially incomplete file: {final_download_path}")
                raise Exception(error_message)
            elif row_count == 0:
                 print(f"Warning: The downloaded CSV file '{final_download_path}' contains 0 rows. This might be expected or indicate no data for the period.")

        except FileNotFoundError:
            print(f"Error: Downloaded file not found at {final_download_path} for row count validation.")
            raise # Re-raise the error as this is unexpected if save_as succeeded
        except Exception as e:
            print(f"Error during CSV row count validation: {e}")
            raise # Re-raise other CSV processing errors
        
        print(f"CSV validation successful. File '{final_download_path}' does not appear to hit the row limit.")
        return final_download_path # Return the path of the downloaded file

    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            if page: 
                screenshot_path = "error_screenshot.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {screenshot_path} on error.")
        except Exception as se:
            print(f"Could not save screenshot: {se}")
    finally:
        print("Closing browser.")
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

    with sync_playwright() as playwright:
        try:
            downloaded_file = run(playwright, args.start_date, args.end_date, args.headless, args.output_name)
            print(f"Script completed successfully. File available at: {downloaded_file}")
        except Exception as e:
            print(f"Script execution failed: {e}")

if __name__ == "__main__":
    main()
