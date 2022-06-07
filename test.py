
import contextlib
from typing import List, Dict


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)
time_format = "%d.%m.%y"

driver.get("https://mangalib.me/i-love-my-daughter-too-much-ill-do-anything-for-her?section=chapters")

import datetime

def find(by: By, value: str):
    """
    I hate this
    """
    with contextlib.suppress(NoSuchElementException):
        return driver.find_element(by=by, value=value)

def get_chapter_data():
    return find(
        By.CLASS_NAME, "media-chapter"
    )

def get_actual_translate(data: Dict[datetime.datetime, str]):
    actual = max(data)
    return data[actual]

#driver.implicitly_wait(5)
chapter_data = get_chapter_data()
print(f"{chapter_data=}")

xpath = '//*[@id="main-page"]/div/div/div/div[2]/div[2]/div[3]/div/div[1]/div[1]/div[2]/div[{i}]'

if chapter_data is None:
    team_list = find(By.CLASS_NAME, "team-list")
    teams: List[WebElement] = team_list.find_elements(By.CLASS_NAME, "team-list-item") # Ищем все переводы
    data = {}
    for i in range(len(teams)):
        team = team_list.find_element(By.XPATH, xpath.format(i=i+1)) # Получаем элемент через XPATH, т.к. иначе на него нельзя нажать
        team.click()
        chapter_data = get_chapter_data()
        dtime = datetime.datetime.strptime(chapter_data.text.splitlines()[2], time_format)
        data[dtime] = driver.current_url

    data = get_actual_translate(data)
    



driver.close()