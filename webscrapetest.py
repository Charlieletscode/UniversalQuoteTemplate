from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import schedule
import pytz
import os
import time
import csv
import pandas as pd

from servertest import insertCommPayment
from servertest import insertWarrPayment, selectByDateCommPayment, selectByDateWarrPayment, insertAuditLog
from servertest import getCredsToken, insertCommPaymentDev, selectCommPaymentDev, selectByDateCommPaymentDev, deleteCommPaymentDev, deleteCommPaymentByDateDev
from servertest import insertWarrPaymentDev, selectWarrPaymentDev, selectByDateWarrPaymentDev, deleteWarrPaymentDev, deleteWarrPaymentByDateDev
from servertest import insertAuditLogDev, selectAuditLogDev, deleteAuditLogDev

chrome_options = Options()
# chrome_options.add_argument("--headless")  # Comment this out to run with GUI
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
webdriver_path = 'chromedriver-win64/chromedriver.exe'  # Update this to your WebDriver path

service = Service(webdriver_path)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

login_url = 'https://interactive.gilbarco.com'
aim_url = 'https://interactive.gilbarco.com/apps/service_reports/warranty_commissions.cfm'

# get in to warranty_commissions
def gillogin(timeout = 5):
    driver.get(login_url)
    username_field = driver.find_element(By.NAME, 'user_id')
    password_field = driver.find_element(By.NAME, 'loginpassword')

    credsDf = getCredsToken("GIL0001")
    username_field.send_keys(credsDf['CUSTNAME'])
    password_field.send_keys(credsDf['Decrypted_Token_Value'])

    login_button = driver.find_element(By.XPATH, '//button[text()="Accept and Login"]')
    login_button.click()
    driver.get(aim_url)
    time.sleep(10)
    if "warranty_commissions" in driver.current_url:
        print("Login successful")
    else:
        print("Failed to login")
    time.sleep(timeout) 
# 2024-01-01 2024-05-28

def gilDatechoose(timeout, formatted_date, warrantyPaymentReportDf, commissionPaymentReportDf):    
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

def gilTransCSV(timeout, current_date, maxretries = 5):
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

def gilScrape(timeout, formatted_date, warrantyPaymentReportDf, commissionPaymentReportDf, current_date):
    dropdown = None
    screenshot_dir = f"log_{current_date}_ss"
    os.makedirs(screenshot_dir, exist_ok=True)  # create folder if not exists

    for attempt in range(3):
        try:
            driver.get(aim_url)
            dropdown = driver.find_element(By.ID, 'sr_selected_branch')
            break  # ✅ success → break retry loop
        except NoSuchElementException:
            print(f"Attempt {attempt + 1}: Could not find the 'sr_selected_branch' dropdown. Retrying in 1 second...")
        except WebDriverException as e:
            print(f"WebDriverException on attempt {attempt+1}: {e}")
       
        time.sleep(1)  # wait before retry

    if not dropdown:
        print("❌ Failed to locate dropdown after 3 attempts.")
        return  # exit gracefully

    # ✅ Continue normal scraping
    initial_select = Select(dropdown)
    options = [(option.get_attribute('value'), option.text) for option in initial_select.options]

    for option_value, option_text in options:
        dropdown = driver.find_element(By.ID, 'sr_selected_branch')
        select = Select(dropdown)
        select.select_by_value(option_value)

        gilDatechoose(timeout=1, formatted_date=formatted_date,
                      warrantyPaymentReportDf=warrantyPaymentReportDf,
                      commissionPaymentReportDf=commissionPaymentReportDf)

        twoDf = gilTransCSV(timeout=1, current_date=current_date)

        if twoDf and not twoDf[0].empty:
            commissionPaymentReportDf = pd.concat([commissionPaymentReportDf, twoDf[0]], ignore_index=True)
            
        if twoDf and not twoDf[1].empty:
            warrantyPaymentReportDf = pd.concat([warrantyPaymentReportDf, twoDf[1]], ignore_index=True)

        print("warrantyypayreport", warrantyPaymentReportDf, "commissionpayreport", commissionPaymentReportDf) 
        time.sleep(timeout)


    # Fill NaN values except for excluded columns
    cols_to_exclude_warranty = ['Check', 'Check_Date']
    warrantyPaymentReportDf = warrantyPaymentReportDf.apply(
        lambda x: x if x.name in cols_to_exclude_warranty else x.fillna(0))

    cols_to_exclude_commission = ['Check']
    commissionPaymentReportDf = commissionPaymentReportDf.apply(
        lambda x: x if x.name in cols_to_exclude_commission else x.fillna(0))
    if(len(warrantyPaymentReportDf) +len(commissionPaymentReportDf) < 0):
        
        # 📸 Save screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshot_dir, f"error_attempt{attempt+1}_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved at {screenshot_path}")
    # else:
        # insertWarrPayment(warrantyPaymentReportDf)  
        # insertCommPayment(commissionPaymentReportDf)
        # warrantyPaymentReportDf.to_csv(f'{formatted_date} Warranty Payment Report.csv', index=False)
        # commissionPaymentReportDf.to_csv(f'{formatted_date} Commission Payment Report.csv', index=False)

# prod
def devscrape():
    try:
        current_dt = datetime.now()   # datetime object
        current_date = current_dt.strftime('%Y-%m-%d')  # string
        previous_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        warrantyPaymentReportDf = pd.DataFrame()
        commissionPaymentReportDf = pd.DataFrame()
        print(len(selectByDateCommPaymentDev(current_date)) + len(selectByDateCommPaymentDev(current_date)))
        max_retries = 6
        attempts = 1
        # Loop while no data exists AND under retry limit
        while (len(selectByDateCommPaymentDev(current_date)) + len(selectByDateCommPaymentDev(current_date)) == 0) and attempts < max_retries:
            gillogin(timeout=1)
            gilScrape(
                timeout=2,
                formatted_date=previous_date,
                warrantyPaymentReportDf=warrantyPaymentReportDf,
                commissionPaymentReportDf=commissionPaymentReportDf,
                current_date=current_date
            )

            # if(len(selectByDateCommPayment(current_date)) + len(selectByDateWarrPayment(current_date)) > 0):
            #     insertAuditLog(status="Success",table_name="WarrPayment",record_count=len(selectByDateWarrPayment(current_date)),timestamp=datetime.now())
            #     insertAuditLog(status="Success",table_name="DateCommPayment",record_count=len(selectByDateCommPayment(current_date)),timestamp=datetime.now())
            #     break
            # else:
            #     insertAuditLog(status="Success",table_name="GilbarcoScraper",record_count=0,timestamp=datetime.now())

            attempts += 1
            print(f"Attempt {attempts} complete. Sleeping before retry...")
            time.sleep(20)  # backoff to avoid hammering
            driver.quit()
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.maximize_window()
            print("Data found, stopping retries.")

    except Exception as e:
        # insertAuditLog(status=e,table_name="GilbarcoScraper",record_count=0,timestamp=datetime.now())
        print(f"An error occurred: {e}. Waiting 100 sec before exit.")
        time.sleep(100)

    finally:
        driver.quit()

# est = pytz.timezone('US/Eastern')
# now = datetime.now(est)
# current_timeAddoneMin = "03:00"
# current_time_add_one_min = now + timedelta(minutes=1)
# # comment following line off to do it at 3 
# current_timeAddoneMin = current_time_add_one_min.strftime("%H:%M")
# print(current_timeAddoneMin)
# schedule.every().day.at(current_timeAddoneMin).do(job)
# def run_scheduler():
#     while True:
#         now = datetime.now(est)
#         current_time = now.strftime("%H:%M")

#         schedule.run_pending()
#         time.sleep(60)

# if __name__ == "__main__":
#     run_scheduler()



