import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def scrape_page_text(driver):
    return {"URL": driver.current_url, "Content": driver.find_element(By.TAG_NAME, "body").text}


def scrape_website_with_nav_links(driver, start_url, output_file):
    driver.get(start_url)
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
                time.sleep(0.5)
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
        "C:\\Users\\raman\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
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
