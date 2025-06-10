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

output_file = "cs_bsc_courses.json"

service = Service("/opt/homebrew/Caskroom/chromedriver/137.0.7151.68/chromedriver-mac-arm64/chromedriver")
print(service)
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 15)

url = "https://campus.tum.de/tumonline/wbstpcs.showSpoTree?pStpStpNr=4998"
driver.get(url)

modules = []

language_button = wait.until(EC.element_to_be_clickable((
    By.CSS_SELECTOR, "button.coa-lang-switcher"
)))
language_button.click()

english_button = wait.until(EC.element_to_be_clickable((
    By.XPATH, "//button[contains(@class, 'mat-mdc-menu-item')]//span[contains(text(), 'EN')]/.."
)))
english_button.click()

time.sleep(2)

required_info = driver.find_element(By.ID, "kn2917691-toggle")
required_info.click()

time.sleep(2)

sub_elements = driver.find_elements(By.CSS_SELECTOR, "a.KnotenLink.noTextDecoration span.KnotenText")

pattern = r"\[(.*?)\]"

for element in sub_elements:
    # Get the module code and name
    text = element.text
    title = element.get_attribute('title')
    match = re.search(pattern, text)
    
    if match and "IN" in match.group(1):
        print(f"Module: {match.group(1)}")
        modules.append(match.group(1))
        print(f"Title: {title}")

required_info.click()

elective_info = driver.find_element(By.ID, "kn2918728-toggle")
elective_info.click()

elements = driver.find_elements(By.XPATH, "//span[@title='Elective subject [Rule node] ']")
ids = [element.find_element(By.XPATH, "..").get_attribute("id") for element in elements]

for id in ids:
    area = driver.find_element(By.ID, id)
    area.click()

    time.sleep(2)

    sub_elements = driver.find_elements(By.CSS_SELECTOR, "a.KnotenLink.noTextDecoration span.KnotenText")

    for element in sub_elements:
        # Get the module code and name
        # if element.get_attribute('id') == 'kn2918920-toggle' or element.get_attribute('id') == 'kn2919162-toggle':
        #     element.click()
        #     time.sleep(2)

        text = element.text
        title = element.get_attribute('title')
        match = re.search(pattern, text)
        
        if match and ("IN" in match.group(1) or "CIT" in match.group(1)):
            print(f"Module: {match.group(1)}")
            modules.append(match.group(1))
            print(f"Title: {title}")
    
    area.click()
    time.sleep(2)

data = {
    "course_codes": modules
}

with open(output_file, 'w') as f:
    json.dump(data, f, indent=4)