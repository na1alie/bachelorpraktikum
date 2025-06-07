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

parsed_links = set()

if Path('content.json').exists():
    with open("content.json", "r", encoding="utf-8") as content_file:
        parsed_content = json.load(content_file)

        for element in parsed_content:
            parsed_links.add(element['url'])
else:
    parsed_content = []
    
service = Service("./chromedriver-linux64/chromedriver")
print(service)
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 15)

url = "https://campus.tum.de/tumonline/wbModHb.wbShow?pOrgNr=1"
driver.get(url)

driver.switch_to.new_window()
driver.switch_to.window(driver.window_handles[0])

print(driver.title)

semester = driver.find_element(By.NAME, 'pFilterSemesterNr')
semesterselect = Select(semester)
semesterselect.select_by_index(0)

pagenr = driver.find_element(By.NAME, 'pPageNr')
pagenrselect = Select(pagenr)

for page in range(380,len(pagenrselect.options)):

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
        link = a.get_attribute('href')
        print(link)

        if not link in parsed_links:
            print(link)
            driver.switch_to.window(driver.window_handles[1])
            driver.get(link)

            try:
                root = driver.find_element(By.XPATH, '//*[@id="ct_tab_DE"]/table/tbody/tr[1]/td[1]/div/table/tbody')
                name = root.find_element(By.XPATH, '//*[text()="Name"]/../../td[2]').text
                kennung = root.find_element(By.XPATH, '//*[text()="Modul-Kennung"]/../../td[2]').text
                anmerkung = root.find_element(By.XPATH, '//*[text()="Anmerkung"]/../../td[2]').text
                lernergebnisse = root.find_element(By.XPATH, '//*[text()="Angestrebte Lernergebnisse"]/../../td[2]').text
                inhalt = root.find_element(By.XPATH, '//*[text()="Inhalt"]/../../td[2]').text

                parsed_content.append({
                    "url": link,
                    "name": name,
                    "kennung": kennung,
                    "anmerkung": anmerkung,
                    "lernergebnisse": lernergebnisse,
                    "inhalt": inhalt
                })
                driver.switch_to.window(driver.window_handles[0])
                print(kennung + ": " + name)

            except NoSuchElementException:
                driver.switch_to.window(driver.window_handles[0])
                print(kennung + ": " + name)

            with open("content.json", "w", encoding="utf-8") as content_file:
                json.dump(parsed_content, content_file, ensure_ascii=False, indent=2)
                content_file.flush()
