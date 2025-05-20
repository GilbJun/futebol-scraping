from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import psutil


def find_if_exists_by_selector(selector, driver):

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        ) 
        return driver.find_elements(By.CSS_SELECTOR, selector)
    except Exception:
        print("Could not get " + selector)
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
    Uploads the team image to Firebase Storage if it does not already exist (by name, regardless of path).
    """
    import requests
    import os
    from google.cloud import storage

    # Set your bucket name (should match your Firebase Storage bucket)
    bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET") or "fufutebol.appspot.com"
    storage_prefix = ""
    storage_path = f"{storage_prefix}{image_name}.png"

    # Initialize Firebase Storage client
    client = storage.Client.from_service_account_json('database/key.json')
    bucket = client.bucket(bucket_name)

    # Check if any blob with this image_name exists in the 'teams/' folder (by name, not just path)
    blobs = bucket.list_blobs(prefix=storage_prefix)
    for blob in blobs:
        if blob.name.endswith(f"{image_name}.png"):
            print("image already exists in storage:", image_name)
            return blob.public_url

    # Download image data
    if imageLink.startswith("http://") or imageLink.startswith("https://"):
        response = requests.get(imageLink)
        image_data = response.content
    else:
        with open(imageLink, "rb") as image_file:
            image_data = image_file.read()

    # Upload to Firebase Storage
    blob = bucket.blob(storage_path)
    blob.upload_from_string(image_data, content_type="image/png")
    # Optionally make public
    # blob.make_public()
    print(f"Uploaded {image_name} to Firebase Storage.")
    return blob.public_url


def count_active_webdrivers():
    webdriver_name = "chromedriver"  # Substitua pelo nome do WebDriver que você está usando
    count = 0
    for process in psutil.process_iter(['name']):
        if webdriver_name in process.info['name']:
            count += 1
    print(f"Active WebDriver instances: {count}")

# from google.cloud import storage
# import os

# def upload_image_to_storage(local_path, storage_path, bucket_name):
#     client = storage.Client.from_service_account_json('database/key.json')
#     bucket = client.bucket(bucket_name)
#     blob = bucket.blob(storage_path)
#     blob.upload_from_filename(local_path)
#     # Optionally make public:
#     # blob.make_public()
#     return blob.public_url 

import time
from selenium.common.exceptions import TimeoutException

def safe_get(driver, url, retries=3, wait=5):
    for attempt in range(retries):
        try:
            driver.get(url)
            return True
        except TimeoutException:
            print(f"Timeout loading {url}, retrying ({attempt+1}/{retries})...")
            time.sleep(wait)
    print(f"Failed to load {url} after {retries} attempts.")
    return False