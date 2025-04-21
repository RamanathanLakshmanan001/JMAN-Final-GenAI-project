import os
import time
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from duckduckgo_search import DDGS  # type: ignore


def find_best_URL(company_name, potential_URLs):
    try:
        prompt = f"""Identify the official website for {company_name} from these options:
        {chr(10).join(potential_URLs)}
        Try to provide the official website URL from the options. Otherwise try to return the most relevant URL among the given options. There should not be any additional text. It should only provide the URL. Also prioritize finance based companies."""

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error processing {company_name}: {str(e)}")
        return None


def search_duckduckgo(query, num_results=3):
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=num_results))
            return [search_result['href'] for search_result in search_results]
    except Exception as e:
        print(f"Error searching DuckDuckGo: {str(e)}")
        return []


def find_official_URL(start_row, end_row):
    dataframe = pd.read_excel(INPUT_FILE)
    companies = dataframe.iloc[start_row:end_row][COMPANY_COLUMN].tolist()

    if os.path.exists(OUTPUT_FILE):
        existing_data = pd.read_excel(OUTPUT_FILE)
    else:
        existing_data = pd.DataFrame(
            columns=["Company Name", "official website URL"])

    official_urls = []
    for i, company in enumerate(companies):
        query = f"{company} official website"
        top_potential_urls = search_duckduckgo(query, num_results=3)

        if not top_potential_urls:
            print(f"No URLs found for {company}")
            official_urls.append(
                {"Company Name": company, "official website URL": "None"})
            continue

        official_url = find_best_URL(company, top_potential_urls)
        official_urls.append(
            {"Company Name": company, "official website URL": official_url})

        updated_data = pd.DataFrame(official_urls)
        combined_data = pd.concat(
            [existing_data, updated_data], ignore_index=True)

        combined_data.to_excel(OUTPUT_FILE, index=False)

        print(f"Processed {i+1}/{len(companies)}: {company}")

        time.sleep(4)

    return pd.DataFrame(official_urls)


if __name__ == "__main__":
    load_dotenv()

    INPUT_FILE = "C:\\JMAN Final Project\\Filtered Company List\\filtered_company_list.xlsx"
    OUTPUT_FILE = "C:\\JMAN Final Project\\Getting Domains\\company_names_with_URL.xlsx"
    COMPANY_COLUMN = "Company Name"

    GEMINI_API_KEY = os.getenv("URL_GEMINI_API_KEY")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    start_row = int(input("Enter the start row (0-based index): "))
    end_row = int(input("Enter the end row (exclusive, 0-based index): "))

    final_dataframe = find_official_URL(start_row, end_row)
    final_dataframe.to_excel(OUTPUT_FILE, index=False)
    print("Processing complete! Extracted URLs saved to", OUTPUT_FILE)
