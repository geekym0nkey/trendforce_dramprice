import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
URL = "https://www.trendforce.com.tw/price/dram/dram_spot"
# Check every 4 hours (4 * 60 * 60 seconds). Adjust as needed.
CHECK_INTERVAL_SECONDS = 1000
OUTPUT_FILENAME = "dram_price_history_FULL.csv"


# NOTE: The table headers are in Chinese: 項目, 日高點, 日低點, 盤高點, 盤低點, 盤平均, 盤漲跌幅

# --- Selenium Setup Function ---
def get_dram_prices():
    # Setup Chrome options for Headless mode (runs in the background)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        # Initialize the WebDriver
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error initializing Chrome driver. Please ensure Chrome is installed and updated. Details: {e}")
        return None

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Navigating to website...")
    driver.get(URL)

    try:
        # 1. Wait until the main price table is visible
        table_selector = "#dram_spot"

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )

        # Find the main price table
        price_table = driver.find_element(By.CSS_SELECTOR, table_selector)

        extracted_data = []

        # 2. Extract Header Row (from <thead>)
        # Find the header row within the table's header section
        header_row = price_table.find_element(By.TAG_NAME, "thead").find_element(By.TAG_NAME, "tr")
        header = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
        extracted_data.append(header)

        # 3. Extract Data Rows (from <tbody>)
        # Find all data rows within the table's body section
        data_rows = price_table.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")

        # Process data rows
        for row in data_rows:
            # Find cells (<td>) in the row
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                row_data = [cell.text.strip() for cell in cells]
                extracted_data.append(row_data)

        # Verification check
        if len(extracted_data) > 1:
            print(f"Successfully extracted {len(extracted_data) - 1} product rows.")

        return extracted_data

    except Exception as e:
        print(f"An error occurred during data extraction (Selector may have changed): {e}")
        return None

    finally:
        # Always close the browser when done
        driver.quit()

# --- Helper Function to Save All Data ---
def save_all_data_to_csv(data, filename):
    """Writes all extracted table data, prepending a timestamp, to a CSV file."""

    # Check if the file already exists to decide whether to write headers
    file_exists = False
    try:
        # Check if the file is not empty (contains at least one character)
        if open(filename, 'r').read(1):
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    try:
        # Use 'a' (append mode)
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # 1. Write Header only if the file is new
            if not file_exists:
                # Add a timestamp column to the header for tracking the check time
                header = data[0]
                writer.writerow(["Timestamp"] + header)
                print(f"Created new file: {filename} with header.")

            # 2. Write Data Rows (starting from the second item in 'data')
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            rows_to_write = 0

            for row in data[1:]:
                # Prepend the timestamp to each data row
                writer.writerow([timestamp] + row)
                rows_to_write += 1

            print(f"Successfully appended {rows_to_write} new entries at {timestamp}.")

    except Exception as e:
        print(f"ERROR saving data to CSV: {e}")


# --- Main Execution Loop ---
if __name__ == "__main__":
    #while True: remove this while loop because I am going to run it on the github action
    data = get_dram_prices()

    if data and len(data) > 1:
            # Pass the full extracted data to the save function
        save_all_data_to_csv(data, OUTPUT_FILENAME)
    else:
        print("Failed to retrieve valid data (or only header found). Skipping save operation.")

    print(f"\nFinished check. Waiting for {CHECK_INTERVAL_SECONDS // 3600} hours...")

        # Wait for the specified interval before checking again
       # time.sleep(CHECK_INTERVAL_SECONDS) ... remove this time.sleep function because we only need to set this in the yml file
