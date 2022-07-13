from interactions import Client

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .mangalib import MangaParser
from .database import DataBaseClient


class MangaLibClient(Client):
    def __init__(self, bot_token: str, mongo_url: str, **kwargs) -> None:
        super().__init__(bot_token, **kwargs)
        self.webdriver: webdriver.Chrome = None
        self.__load_webdriver()
        self.parser = MangaParser(self.webdriver)
        self.database = DataBaseClient(mongo_url)

    def __load_webdriver(self):
        options = Options()
        options.add_argument("--headless")
        self.webdriver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
