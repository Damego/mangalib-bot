from interactions import Client

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class MangaLibClient(Client):
    def __init__(self, token: str, **kwargs) -> None:
        super().__init__(token, **kwargs)
        self.webdriver: webdriver.Chrome = None
        self.__load_webdriver()

    def __load_webdriver(self):
        options = Options()
        options.add_argument("--headless")
        self.webdriver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
