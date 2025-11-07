from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import shutil
import pandas as pd
import time, os, pytz

from servertest import (
    getCredsToken,
    insertWarrPayment, insertCommPayment, selectByDateWarrPayment, selectByDateCommPayment,
    insertWarrPaymentDev, insertCommPaymentDev, selectByDateWarrPaymentDev, selectByDateCommPaymentDev,
    insertAuditLogDev, insertAuditLog
)

LOGIN_URL = "https://interactive.gilbarco.com"
AIM_URL = "https://interactive.gilbarco.com/apps/service_reports/warranty_commissions.cfm"


# -------------------------------
# 🧰 Utility Functions
# -------------------------------

def create_driver(headless=True):
    """Auto-updates ChromeDriver to match current Chrome."""
    # Clear cached drivers if they exist
    cache_path = os.path.join(os.path.expanduser("~"), ".wdm")
    if os.path.exists(cache_path):
        try:
            shutil.rmtree(cache_path)
            print("🧹 Old ChromeDriver cache cleared.")
        except Exception as e:
            print(f"⚠️ Could not clear cache: {e}")

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    print("🔍 Checking for compatible ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    print("✅ ChromeDriver launched successfully.")
    return driver


def gilDatechoose(driver, timeout, formatted_date, warrantyPaymentReportDf, commissionPaymentReportDf):    
    from_date_field = driver.find_element(By.CSS_SELECTOR, 'input#from_date')
    driver.execute_script("arguments[0].removeAttribute('readonly')", from_date_field)
    from_date_field.send_keys(formatted_date)
    driver.execute_script("arguments[0].value = arguments[1];", from_date_field, formatted_date)
    updated_value = from_date_field.get_attribute('value')
    print(f"Updated value: {updated_value}")
    done_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all[data-handler="hide"][data-event="click"]'))
    )
    done_button.click()
    
    to_date_field = driver.find_element(By.CSS_SELECTOR, 'input#to_date')
    driver.execute_script("arguments[0].removeAttribute('readonly')", to_date_field)
    to_date_field.send_keys(formatted_date)
    driver.execute_script("arguments[0].value = arguments[1];", to_date_field, formatted_date)
    updated_value = to_date_field.get_attribute('value')
    print(f"Updated value: {updated_value}")
    done_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all[data-handler="hide"][data-event="click"]'))
    )
    done_button.click()

    process_button = driver.find_element(By.XPATH, '//button[text()="Process"]')
    process_button.click()
    time.sleep(timeout)

def gilTransCSV(driver, timeout, current_date, maxretries = 5):
    retry = 0
    while retry < maxretries:
        try:
            tables = driver.find_elements(By.CSS_SELECTOR, 'div.issue-listing-table.small.open-service-calls')
            df = pd.DataFrame()
            twoDf = [df, df]
            header_names = None

            for index in range(len(tables)):
                headers = tables[index].find_elements(By.CSS_SELECTOR, 'thead th')
                header_names = [header.text for header in headers]
                header_names.pop(0)
                header_names.insert(0, "ASC")
                header_names.insert(1, "DateExecution")
                rows = tables[index].find_elements(By.CSS_SELECTOR, 'tbody tr')

                time.sleep(10)
                dropdown = driver.find_element(By.ID, 'sr_selected_branch')
                select = Select(dropdown)
                selected_option = select.first_selected_option
                table_data = []

                for row in rows:
                    if 'spacer' in row.get_attribute('class'):
                        continue

                    td_elements = row.find_elements(By.CSS_SELECTOR, 'td')
                    row_data = [selected_option.get_attribute('value'), current_date]

                    for td in td_elements:
                        try:
                            nested_td = td.find_element(By.CSS_SELECTOR, 'table tbody tr')
                            row_data.append(nested_td.text.strip())
                        except NoSuchElementException:
                            continue

                    if any(row_data) and len(row_data) == len(header_names):
                        table_data.append(row_data)

                df = pd.DataFrame(table_data, columns=header_names)

                if header_names and "Commission" in header_names:
                    twoDf[0] = pd.concat([twoDf[0], df], ignore_index=True)
                elif header_names and "Labor Cost" in header_names:
                    twoDf[1] = pd.concat([twoDf[1], df], ignore_index=True)

            return twoDf  # ✅ success, return here
        except Exception as e:
            print(f"Retry {retry + 1} failed: {e}")
            retry += 1
            time.sleep(5)  # optional wait between retries

    print("❌ Max retries reached. Data could not be extracted.")
    return [pd.DataFrame(), pd.DataFrame()]

def safe_quit(driver):
    """Safely quits Chrome."""
    try:
        if driver:
            driver.quit()
    except Exception:
        pass


def gilbarco_login(driver):
    if driver is None:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.maximize_window()
    """Logs into the Gilbarco Interactive portal."""
    creds = getCredsToken("GIL0001")
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "user_id")))

    driver.find_element(By.NAME, "user_id").send_keys(creds["CUSTNAME"])
    driver.find_element(By.NAME, "loginpassword").send_keys(creds["Decrypted_Token_Value"])
    driver.find_element(By.XPATH, '//button[text()="Accept and Login"]').click()

    WebDriverWait(driver, 30).until(lambda d: "gilbarco.com" in d.current_url)
    driver.get(AIM_URL)
    time.sleep(3)
    print("✅ Logged into Gilbarco portal.")


def gilbarco_scrape(driver, formatted_date, current_date, dev=True, timeout=5):
    """Scrape one day of Gilbarco warranty + commission reports."""
    warrantyPaymentReportDf, commissionPaymentReportDf = pd.DataFrame(), pd.DataFrame()
    screenshot_dir = f"log_{current_date}_ss"
    os.makedirs(screenshot_dir, exist_ok=True)

    # find dropdown with retry
    dropdown = None
    for attempt in range(3):
        try:
            driver.get(AIM_URL)
            dropdown = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "sr_selected_branch"))
            )
            break
        except Exception as e:
            print(f"Attempt {attempt+1}: dropdown not found ({e}). Retrying...")
            time.sleep(2)
    if not dropdown:
        print("❌ Dropdown not found after 3 attempts.")
        return

    # iterate branches
    initial_select = Select(dropdown)
    options = [(option.get_attribute('value'), option.text) for option in initial_select.options]

    for option_value, option_text in options:
        dropdown = driver.find_element(By.ID, 'sr_selected_branch')
        select = Select(dropdown)
        select.select_by_value(option_value)

        gilDatechoose(driver=driver, timeout=1, formatted_date=formatted_date,
                      warrantyPaymentReportDf=warrantyPaymentReportDf,
                      commissionPaymentReportDf=commissionPaymentReportDf)

        twoDf = gilTransCSV(driver=driver, timeout=1, current_date=current_date)

        if twoDf and not twoDf[0].empty:
            commissionPaymentReportDf = pd.concat([commissionPaymentReportDf, twoDf[0]], ignore_index=True)
            
        if twoDf and not twoDf[1].empty:
            warrantyPaymentReportDf = pd.concat([warrantyPaymentReportDf, twoDf[1]], ignore_index=True)

        print("warrantyypayreport", warrantyPaymentReportDf, "commissionpayreport", commissionPaymentReportDf) 
        time.sleep(timeout)
    # ✅ Safe insert section
    if not commissionPaymentReportDf.empty:
        print(f"💰 Inserting {len(commissionPaymentReportDf)} commission rows.")
        (insertCommPaymentDev if dev else insertCommPayment)(commissionPaymentReportDf)
    else:
        print("⚠️ No commission data found — skipping.")

    if not warrantyPaymentReportDf.empty:
        print(f"🧾 Inserting {len(warrantyPaymentReportDf)} warranty rows.")
        (insertWarrPaymentDev if dev else insertWarrPayment)(warrantyPaymentReportDf)
    else:
        print("⚠️ No warranty data found — skipping warranty insert.")


# -------------------------------
# 🚀 Main Scraper Runners
# -------------------------------
def devscrape():
    """Development version: uses Dev tables."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    formatted_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    for attempt in range(1, 6):
        driver = None
        try:
            print(f"🚀 Dev run attempt {attempt}/5 for {formatted_date}")
            driver = create_driver(headless=False)
            gilbarco_login(driver)
            gilbarco_scrape(driver, formatted_date, current_date, dev=True)
            insertAuditLogDev("SUCCESS", "GilbarcoScraperDev", 1, datetime.now())
            print("✅ Dev scrape completed successfully.")
            break
        except Exception as e:
            print(f"❌ Dev attempt {attempt} failed: {e}")
            insertAuditLogDev("FAILED", "GilbarcoScraperDev", 0, f"Dev attempt {attempt} failed: {e}", datetime.now())
            time.sleep(10)
        finally:
            safe_quit(driver)


def prodscrape():
    """Production version: writes to live tables."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    formatted_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    for attempt in range(1, 6):
        driver = None
        try:
            print(f"🚀 Prod run attempt {attempt}/5 for {formatted_date}")
            driver = create_driver(headless=True)
            gilbarco_login(driver)
            gilbarco_scrape(driver, formatted_date, current_date, dev=False)
            insertAuditLog("SUCCESS", "GilbarcoScraper", 1, datetime.now())
            print("✅ Prod scrape completed successfully.")
            break
        except Exception as e:
            print(f"❌ Prod attempt {attempt} failed: {e}")
            insertAuditLog("FAILED", "GilbarcoScraper", 0, datetime.now())
            time.sleep(10)
        finally:
            safe_quit(driver)


if __name__ == "__main__":
    # toggle here
    DEV_MODE = True
    if DEV_MODE:
        devscrape()
    else:
        prodscrape()
