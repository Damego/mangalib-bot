import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .models import *


time_format = "%d.%m.%Y"
xpath = '//*[@id="main-page"]/div/div/div/div[2]/div[2]/div[3]/div/div[1]/div[1]/div[2]/div[{i}]'


class MangaParser:
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.driver = driver
        self.is_busy = False

    def parse_manga_data(self, name: str) -> MangaData | None:
        search_url = f"https://mangalib.me/manga-list?sort=rate&dir=desc&page=1&name={name.replace(' ', '%20')}"

        # Getting url of manga
        self.driver.get(url=search_url)
        try:
            url = self.driver.find_element(By.CLASS_NAME, "media-card").get_attribute(
                "href"
            )
        except NoSuchElementException:
            return
        self.driver.get(url=url)

        # Getting data of manga
        data = {
            "name": self.driver.find_element(By.CLASS_NAME, "media-name__main").text
        }
        score_data = self.driver.find_element(
            By.CLASS_NAME, "media-rating-wrap"
        ).text.splitlines()
        data["score"] = {"score": score_data[0], "count": score_data[1]}
        data_raw = self.driver.find_element(
            By.CLASS_NAME, "media-info-list"
        ).text.splitlines()
        data["info"] = {
            data_raw[i]: data_raw[i + 1] for i in range(0, len(data_raw) - 1, 2)
        }
        image_card = self.driver.find_element(By.CLASS_NAME, "media-sidebar__cover")
        data["image_url"] = image_card.find_element(By.XPATH, "img").get_attribute(
            "src"
        )
        data["first_chapter"] = {
            "name": None,
            "url": (
                self.driver.find_element(By.CLASS_NAME, "media-sidebar__buttons")
                .find_element(By.XPATH, "a")
                .get_attribute("href")
            ),
        }
        data["description"] = self.driver.find_element(
            By.CLASS_NAME, "media-description__text"
        ).text
        data["genres"] = self.driver.find_element(
            By.CLASS_NAME, "media-tags"
        ).text.splitlines()

        self.driver.get(url=f"{url}?section=chapters")
        last_chapter_data = self._get_last_chapter_data()
        data["last_chapter"] = last_chapter_data
        data["url"] = url

        return MangaData(**data)

    def _get_last_chapter_data(self):
        try:
            chapter_data = self.driver.find_element(By.CLASS_NAME, "media-chapter")
            chapter_data = chapter_data.find_element(By.CLASS_NAME, "link-default")
            chapter_name = chapter_data.text.splitlines()
            if not chapter_name:
                return
            chapter_name = chapter_name[0]
            chapter_url = chapter_data.get_attribute("href")
        except NoSuchElementException:  # У манги несколько переводов, поэтому страница пустая
            return self.get_chapter_from_team()
        return {"name": chapter_name, "url": chapter_url}

    def get_latest_chapter(self):
        chapters = self.driver.find_elements(
            By.CLASS_NAME, "vue-recycle-scroller__item-view"
        )
        for chapter in chapters:
            attr = chapter.get_attribute("style")
            if attr == "transform: translateY(0px);":
                return chapter.find_element(By.CLASS_NAME, "media-chapter")

    def get_chapter_from_team(self):
        team_list = self.driver.find_element(By.CLASS_NAME, "team-list")
        teams: list[WebElement] = team_list.find_elements(
            By.CLASS_NAME, "team-list-item"
        )  # Ищем все переводы
        data = {}

        for i in range(len(teams)):
            team = team_list.find_element(
                By.XPATH, xpath.format(i=i + 1)
            )  # Получаем элемент через XPATH, т.к. иначе на него нельзя нажать
            team.click()

            chapter = self.get_latest_chapter()
            chapter_url = chapter.find_element(
                By.CLASS_NAME, "link-default"
            ).get_attribute("href")
            chapter_data = chapter.text.splitlines()
            time = chapter_data[2]
            dtime = datetime.datetime.strptime(time, time_format)
            data[dtime] = {"name": chapter_data[0], "url": chapter_url}
        return self.get_chapter_by_time(data)

    def get_chapter_by_time(self, data: dict[datetime.datetime, dict[str, str]]):
        actual = max(data)
        return data[actual]

    def check_new_chapter(self, url: str) -> Chapter:
        if "section=chapters" not in url:
            url += "?section=chapters"
        self.driver.get(url)
        chapter_data = self._get_last_chapter_data()
        return Chapter(**chapter_data)

    def base64_from_url(self, url: str):
        self.driver.get(url)
        base64 = self.driver.find_element(
            By.XPATH, "/html/body/img"
        ).screenshot_as_base64
        return base64
