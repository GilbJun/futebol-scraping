from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

def find_if_exists_by_selector(selector, driver):
    try:
        return driver.find_elements(By.CSS_SELECTOR, selector)
    except NoSuchElementException:
        return False

def chunk_dict(data, n):
    items = list(data.items())
    return [dict(items[i::n]) for i in range(n)]


def image_link_to_base64String(imageLink):
    import base64
    import requests
    import os

    if imageLink.startswith("http://") or imageLink.startswith("https://"):
        response = requests.get(imageLink)
        image_data = response.content
    else:
        with open(imageLink, "rb") as image_file:
            image_data = image_file.read()

    base64_string = base64.b64encode(image_data).decode('utf-8')
    return base64_string