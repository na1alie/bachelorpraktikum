from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

input_file = "cs_bsc_courses.json"
output_file = "cs_bsc_courses_info.json"

modules = []

# Reading the JSON file
with open(input_file, 'r') as f:
    loaded_data = json.load(f)
    
# Access the codes
codes = loaded_data["course_codes"]

service = Service("/opt/homebrew/Caskroom/chromedriver/137.0.7151.68/chromedriver-mac-arm64/chromedriver")
print(service)
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 15)

url = "https://campus.tum.de/tumonline/wbModHb.wbShow?pOrgNr=1"
driver.get(url)

language_button = wait.until(EC.element_to_be_clickable((
    By.CSS_SELECTOR, "button.coa-lang-switcher"
)))
language_button.click()

english_button = wait.until(EC.element_to_be_clickable((
    By.XPATH, "//button[contains(@class, 'mat-mdc-menu-item')]//span[contains(text(), 'EN')]/.."
)))
english_button.click()

time.sleep(2)

driver.switch_to.new_window()
driver.switch_to.window(driver.window_handles[0])

for code in codes:
    print(code)
    id = driver.find_element(By.NAME, 'pFilterNameOrKennung')
    id.clear()
    id.send_keys(code)

    filter_button = driver.find_element(By.ID, 'idModHbFilterButton')
    filter_button.click()

    time.sleep(2)

    try:
        content = driver.find_element(By.ID, 'idModHBTable')
    except NoSuchElementException:
        content = driver.find_element(By.ID, 'idModHBTableORG')

    tbody = content.find_element(By.TAG_NAME, 'tbody')
    trs = tbody.find_elements(By.TAG_NAME, 'tr')

    for tr in trs:
        td = tr.find_element(By.TAG_NAME, 'td')
        a = td.find_elements(By.TAG_NAME, 'a')[1]
        link = a.get_attribute('href')

        print(link)
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)

        time.sleep(2)

        try:
            root = driver.find_element(By.XPATH, '//*[@id="ct_tab_EN"]/table/tbody/tr[1]/td[1]/div/table/tbody')
            name = root.find_element(By.XPATH, '//*[text()="Name"]/../../td[2]').text
            kennung = root.find_element(By.XPATH, "//label[contains(text(), 'Module ID')]/../../td[2]").text
            anmerkung = root.find_element(By.XPATH, '//*[text()="Comment"]/../../td[2]').text
            lernergebnisse = root.find_element(By.XPATH, '//*[text()="Intended Learning Outcomes"]/../../td[2]').text
            inhalt = root.find_element(By.XPATH, '//*[text()="Content"]/../../td[2]').text
            prerequisites = root.find_element(By.XPATH, '//*[text()="Prerequisites (recommended)"]/../../td[2]').text

            modules.append({
                "url": link,
                "name": name,
                "kennung": kennung,
                "anmerkung": anmerkung,
                "lernergebnisse": lernergebnisse,
                "inhalt": inhalt,
                "prerequisites": prerequisites
            })
            driver.switch_to.window(driver.window_handles[0])
            print(kennung + ": " + name)

        except NoSuchElementException:
            driver.switch_to.window(driver.window_handles[0])
            print(kennung + ": " + name)

with open(output_file, 'w') as f:
    json.dump(modules, f, indent=4)
