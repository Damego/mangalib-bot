from selenium import webdriver
from selenium.webdriver.common.by import By


def load_manga_data(driver: webdriver.Chrome, name: str):
    search_url = f"https://mangalib.me/manga-list?sort=rate&dir=desc&page=1&name={name.replace(' ', '%20')}"

    # Getting url of manga
    driver.get(url=search_url)
    try:
        url = driver.find_element(By.CLASS_NAME, "media-card").get_attribute("href")
    except Exception:
        return

    # Getting data of manga
    driver.get(url=f"{url}?section=chapters")

    score_data = driver.find_element(
        By.CLASS_NAME, "media-rating-wrap"
    ).text.splitlines()
    score, count = score_data[0], score_data[1]

    data_raw = driver.find_element(By.CLASS_NAME, "media-info-list").text.splitlines()
    data = {data_raw[i]: data_raw[i + 1] for i in range(0, len(data_raw) - 1, 2)}

    image_card = driver.find_element(By.CLASS_NAME, "media-sidebar__cover")
    image_url = image_card.find_element(By.XPATH, "img").get_attribute("src")
    print(image_url)

    full_name = driver.find_element(By.CLASS_NAME, "media-name__main").text

    first_chapter_url = (
        driver.find_element(By.CLASS_NAME, "media-sidebar__buttons")
        .find_element(By.XPATH, "a")
        .get_attribute("href")
    )
    last_chapter_data = driver.find_element(
        By.CLASS_NAME, "media-chapter__name"
    ).find_element(By.CLASS_NAME, "link-default")
    last_chapter_name = last_chapter_data.text
    last_chapter_url = last_chapter_data.get_attribute("href")

    driver.get(url=f"{url}?section=info")

    description = driver.find_element(By.CLASS_NAME, "media-description__text").text
    genres = driver.find_element(By.CLASS_NAME, "media-tags").text.splitlines()

    driver.get(url=f"{url}?section=chapters")
    new_url, last_chapter_data = _parse_last_chapter(driver)
    if new_url is not None:
        url = new_url

    return {
        "name": full_name,
        "description": description,
        "image_url": image_url,
        "info": data,
        "genres": genres,
        "url": url,
        "score_info": {"score": score, "count": count},
        "first_chapter_url": first_chapter_url,
        "last_chapter": {"name": last_chapter_name, "url": last_chapter_url},
    }

def _parse_last_chapter(driver: webdriver.Chrome, url: str = None):
    try:
        chapter_data = driver.find_element(
            By.CLASS_NAME, "media-chapter"
        )
        print(chapter_data.text)
        chapter_data = chapter_data.find_element(By.CLASS_NAME, "link-default")
        chapter_name = chapter_data.text.splitlines()[0]
        chapter_url = chapter_data.get_attribute("href")
    except NoSuchElementException: # У манги несколько переводов, поэтому страница пустая
        new_url = get_new_url(driver)
        return _parse_last_chapter(driver, new_url)
    return url, {"name": chapter_name, "url": chapter_url}

def get_new_url(driver: webdriver.Chrome):
    team_list = driver.find_element(By.CLASS_NAME, "team-list")
    teams: List[WebElement] = team_list.find_elements(By.CLASS_NAME, "team-list-item") # Ищем все переводы
    data = {}
    for i in range(len(teams)):
        team = team_list.find_element(By.XPATH, xpath.format(i=i+1)) # Получаем элемент через XPATH, т.к. иначе на него нельзя нажать
        team.click()
        chapter_data = get_all_chapter_data(driver)
        time = chapter_data.text.splitlines()[2]
        dtime = datetime.datetime.strptime(time, time_format)
        data[dtime] = driver.current_url

    return get_actual_translate(data)


def get_actual_translate(data: Dict[datetime.datetime, str]):
    actual = max(data)
    return data[actual]


def get_all_chapter_data(driver: webdriver.Chrome):
    return driver.find_element(
        By.CLASS_NAME, "media-chapter"
    )


def check_new_chapter(driver: webdriver.Chrome, url: str):
    driver.get(url)
    chapter_data = driver.find_element(
        By.CLASS_NAME, "media-chapter__name"
    ).find_element(By.CLASS_NAME, "link-default")
    chapter_name = chapter_data.text
    chapter_url = chapter_data.get_attribute("href")

    data = {"name": chapter_name, "url": chapter_url}
    return data


def base64_from_url(driver: webdriver.Chrome, url: str):
    driver.get(url)
    base64 = driver.find_element(By.XPATH, "/html/body/img").screenshot_as_base64
    return base64
