import os
import time
import pandas as pd
from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore


def scroll_to_bottom(driver, pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height


def scrape_page_text(driver):
    return {"URL": driver.current_url, "Content": driver.find_element(By.TAG_NAME, "body").text}


def scrape_website_with_nav_links(driver, start_url, output_file):
    driver.get(start_url)
    scroll_to_bottom(driver)
    time.sleep(0.5)
    data = [scrape_page_text(driver)]
    links_to_visit = set()

    navbar_links = driver.find_elements(By.CSS_SELECTOR, "nav a")
    for link in navbar_links:
        href = link.get_attribute("href")
        if href:
            links_to_visit.add(href)

    header_links = driver.find_elements(By.CSS_SELECTOR, "header a")
    for link in header_links:
        href = link.get_attribute("href")
        if href:
            links_to_visit.add(href)

    footer_links = driver.find_elements(By.CSS_SELECTOR, "footer a")
    for link in footer_links:
        href = link.get_attribute("href")
        if href:
            links_to_visit.add(href)

    visited = set()
    for href in links_to_visit:
        if href not in visited:
            visited.add(href)
            try:
                driver.get(href)
                scroll_to_bottom(driver)
                time.sleep(4)
                data.append(scrape_page_text(driver))
            except Exception as e:
                print(f"Error visiting {href}: {e}")

    pd.DataFrame(data).to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")


def clean_company_name(company_name):
    company_name = company_name.replace("/", "-")
    company_name = company_name.replace(" ", "_")
    return company_name


if __name__ == "__main__":
    excel_file = "C:\\JMAN Final Project\\Getting Domains\\company_names_with_URL.xlsx"
    output_dir = "C:\\JMAN Final Project\\Scraping Data\\Scraped Data from websites"
    os.makedirs(output_dir, exist_ok=True)

    data = pd.read_excel(excel_file)

    start_row = int(input("Enter the start row (0-based index): "))
    end_row = int(input("Enter the end row (exclusive, 0-based index): "))

    data_to_process = data.iloc[start_row:end_row]
    company_names = data_to_process["Company Name"]
    urls = data_to_process["official website URL"]

    service = Service(
        "C:\\Users\\RamanathanL\\Downloads\\chromedriver-win64\\chromedriver.exe")
    chrome_options = Options()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        for company, url in zip(company_names, urls):
            cleaned_company_name = clean_company_name(company)
            output_file = os.path.join(
                output_dir, f"Scraped_data_{cleaned_company_name}.csv")
            print(f"Scraping data for: {company} ({url})")
            try:
                scrape_website_with_nav_links(driver, url, output_file)
            except Exception as e:
                print(f"Error scraping website {url}: {e}")
    finally:
        driver.quit()
        print("Scraping completed.")
