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

def save_team_image(imageLink, image_name):
    """
    Baixa a imagem do time e salva como PNG no caminho files/images/team/{slug}.png
    """
    import requests
    import os


    if os.path.exists("files/images/teams/" + image_name):
        print("image already exists", image_name)
        return

    if imageLink.startswith("http://") or imageLink.startswith("https://"):
        response = requests.get(imageLink)
        image_data = response.content
    else:
        with open(imageLink, "rb") as image_file:
            image_data = image_file.read()
    
    output_dir = os.path.join("files", "images", "teams")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{image_name}.png")
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path