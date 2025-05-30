from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

service = Service("./chromedriver-linux64/chromedriver")
print(service)
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 15)

url = "https://campus.tum.de/tumonline/wbModHb.wbShow?pOrgNr=1"
driver.get(url)

print(driver.title)

pagenr = driver.find_element(By.NAME, 'pPageNr')
pagenrselect = Select(pagenr)

for page in range(len(pagenrselect.options)):

    if pagenrselect.first_selected_option != pagenrselect.options[page]:
        pagenrselect.select_by_index(page)

        wait.until(EC.staleness_of(pagenr))

        pagenr = driver.find_element(By.NAME, 'pPageNr')
        pagenrselect = Select(pagenr)

    try:
        content = driver.find_element(By.ID, 'idModHBTable')
    except NoSuchElementException:
        content = driver.find_element(By.ID, 'idModHBTableORG')

    tbody = content.find_element(By.TAG_NAME, 'tbody')
    trs = tbody.find_elements(By.TAG_NAME, 'tr')

    for tr in trs:
        td = tr.find_element(By.TAG_NAME, 'td')
        a = td.find_elements(By.TAG_NAME, 'a')[1]
        print(a.get_attribute('href'))

