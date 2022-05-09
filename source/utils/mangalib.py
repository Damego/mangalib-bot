from selenium import webdriver
from selenium.webdriver.common.by import By


def load_manga_data(driver: webdriver.Chrome, name: str):
    search_url = f"https://mangalib.me/manga-list?sort=rate&dir=desc&page=1&name={name.replace(' ', '%20')}"

    # Getting url of manga
    driver.get(url=search_url)
    manga_url = driver.find_element(By.CLASS_NAME, "media-card")
    t = manga_url.text
    manga_url = manga_url.get_attribute("href")
    if manga_url is None:
        print("ХАНА МАШИНЕ")
        return

    # Getting data of manga

    driver.get(url=f"{manga_url}?section=chapters")
    score_data = driver.find_element(By.CLASS_NAME, "media-rating-wrap").text.splitlines()
    score, count = score_data[0], score_data[1]
    manga_data = driver.find_element(By.CLASS_NAME, "media-info-list").text.splitlines()
    manga_image = driver.find_element(
        By.XPATH, '//*[@id="main-page"]/div/div[2]/div/div[1]/div[1]/div/img'
    ).get_attribute("src")
    manga_data = {
        manga_data[i]: manga_data[i + 1] for i in range(0, len(manga_data) - 1, 2)
    }
    full_name = driver.find_element(By.CLASS_NAME, "media-name__main").text
    last_chapter_data = driver.find_element(
        By.CLASS_NAME, "media-chapter__name"
    ).find_element(By.CLASS_NAME, "link-default")

    last_chapter_name = last_chapter_data.text
    last_chapter_url = last_chapter_data.get_attribute("href")

    driver.get(url=f"{manga_url}?section=info")
    description = driver.find_element(By.CLASS_NAME, "media-description").text
    genres = driver.find_element(By.CLASS_NAME, "media-tags").text.splitlines()

    data = {
        "name": full_name,
        "description": description,
        "image_url": manga_image,
        "manga_info": manga_data,
        "genres": genres,
        "score_info": {
            "score": score,
            "count": count
        },
        "last_chapter": {"name": last_chapter_name, "url": last_chapter_url},
    }
    return data
