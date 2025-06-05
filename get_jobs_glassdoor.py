from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

# Your Glassdoor credentials
GLASSDOOR_EMAIL = "vobaxev134@eduhed.com"
GLASSDOOR_PASSWORD = "glassdoor123456"

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
# options.add_argument("--headless")  # Don't use headless for login

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

try:
    driver.get("https://www.glassdoor.com/profile/login_input.htm")

    # Wait until the email input is visible and fill it
    email_input = wait.until(EC.visibility_of_element_located((By.ID, "inlineUserEmail")))
    email_input.send_keys(GLASSDOOR_EMAIL)
        
    # # Click the continue with email button
    continue_with_email_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[@type='submit' and @data-test='continue-with-email-modal']")))
    # continue_with_email_button = driver.find_element(By.XPATH, "//button[@type='submit' and @data-test='continue-with-email-modal']")
    continue_with_email_button.click()

    # Fill password
    password_input = wait.until(EC.visibility_of_element_located((By.ID, "inlineUserPassword")))
    password_input.send_keys(GLASSDOOR_PASSWORD)

    # Click the sign-in button
    sign_in_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    sign_in_button.click()

    # Wait for some element that is visible only after login to confirm success
    wait.until(EC.presence_of_element_located((By.ID, "SiteNav")))

    print("✅ Logged in successfully!")

    # Now you can go to job search page or scrape
    driver.get("https://www.glassdoor.com/Job/jobs.htm?sc.keyword=data+scientist")
    time.sleep(5)
    print(driver.page_source[:1000])

finally:
    driver.quit()
