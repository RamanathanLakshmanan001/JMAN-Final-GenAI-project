## Overview

This application extracts and aggregates company information from various online sources. The process involves four main steps:

1. Extracting domain names from company data using `URL_finder.py`
2. Scraping company details from these domains using `scraper.py`
3. Translating the scraped data and storing it as embeddings using `translate_and_store_embeddings.py`
4. Extracting the required information using `extract_answers.py`

## Prerequisites

1. **Python 3.8+**
   - Ensure that you are using Python 3.8 or higher for compatibility with all required packages.

2. **Required Python Packages**
   - Install the following packages via `pip`:
     ```bash
     pip install pandas google-generativeai python-dotenv duckduckgo-search selenium deep-translator pinecone sentence-transformers
     ```

3. **Gemini API Key**
   - You'll need a Gemini API Key.

4. **Pinecone**
   - You'll need a Pinecone API Key.
   - You'll need a Pinecone index.

## Usage

**Step 1: Extract Domain Names**

1. Enter the company name whose information need to be obtained in the second column of the `filtered_company_list.xlsx`

2. Run the `URL_finder.py` script using the following command:

```bash
python URL_finder.py
```

3. Enter the range of rows that needs to be processed. The program is using 0-based indexing. Enter the start row as (actual start row-2). Enter the end row as (actual end row-1)

   - Example: The actual start row in the excel is `35` and actual end row is `43`, you have to enter the start row as `33` and end row as `42`.

**Input file:**
`filtered_company_list.xlsx`

**Output file:**
`company_names_with_URL.xlsx`

**Step 2: Scrape Company Details**

1. Run the `scraper.py` using the following command:
        
```bash
python scraper.py
```
2. Enter the range of rows that needs to be processed. The program is using 0-based indexing. Enter the start row as (actual start row-2). Enter the end row as (actual end row-1)

   - Example: The actual start row in the excel is `35` and actual end row is `43`, you have to enter the start row as `33` and end row as `42`.

**Input file:**
`company_names_with_URL.xlsx` 

**Output file:**
`Scraped_data_<cleaned_company_name>.csv` 

**Step 3: Translate and store the scraped data**

1. Run the `translate_and_store_embeddings.py` using the following command:

```bash
python translate_and_store_embeddings.py
```
2. Enter the range of rows that needs to be processed. The program is using 0-based indexing. Enter the start row as (actual start row - 2). Enter the end row as (actual end row - 1)

   - Example: The actual start row in the Excel is `35` and the actual end row is `43`, you have to enter the start row as `33` and the end row as `42`.


**Input file:**
`Scraped_data_<cleaned_company_name>.csv` 

**Output:**
Embeddings in Pinecone DB

**Step 4: Extract Required Information**

1. Run the `extract_answers.py` using the following command:
        
```bash
python extract_answers.py
```

**Input file:**
`company_names_with_URL.xlsx` 

**Output file:**
`details_of_companies.xlsx`

## Challenges Faced

1. The official websites of some companies can't be found, which makes the process of finding the details of the company difficult.

2. While trying to get the official website of the company using SerpApi, I get some other websites.

   - Example: The company name is INDUNA. The official website of the company is `https://www.groupinduna.com/`
     en/. The website that I got is `https://www.indunamusic.com/`.

3. A few websites are dynamically rendering. The scraping process is completed before the elements are rendered, which results in loss of information.

4. The scraping process consumes too much time.

5. Although the required information is scraped and stored in pinecone db as embeddings, the best match or the most relevant information can't be obtained when trying to fetch the matches from pinecone.

6. Most of the third-party APIs available are asking for paid versions to get financial data of companies.

7. The Gemini API used has a quota limit of 1500 queries per day, which is less than the 2305 queries that need to be made to get the company information

## Third-Party websites tried

- Crunchbase

- Pitchbook













