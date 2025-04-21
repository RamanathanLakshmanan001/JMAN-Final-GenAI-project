import os
import csv
import hashlib
import pandas as pd

from dotenv import load_dotenv
from deep_translator import GoogleTranslator  # type: ignore
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

def generate_vector_id(company_name):
    return hashlib.md5(company_name.encode('utf-8')).hexdigest()

def clean_company_name(company_name):
    company_name = company_name.replace("/", "-")
    company_name = company_name.replace(" ", "_")
    return company_name


def divide_chunks(text, chunk_size=200, overlap=100):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def translate_text(text, max_length=4500):
    if len(text) <= max_length:
        return GoogleTranslator(source='auto', target='en').translate(text)
    
    result = ""
    chunks = []
    current_chunk = ""
    words = text.split()
    
    for word in words:
        if len(current_chunk) + len(word) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word
    
    if current_chunk:
        chunks.append(current_chunk)
    
    for i, chunk in enumerate(chunks):
        translated_chunk = GoogleTranslator(source='auto', target='en').translate(chunk)
        result += translated_chunk + " "
    
    return result.strip()

def main():
    load_dotenv()
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = os.getenv("PINECONE_ENV")

    pc = Pinecone(api_key=PINECONE_API_KEY,environment=PINECONE_ENV)
    index_name = "translated-embeddings"
    index = None

    try:
        index = pc.Index(index_name)
        print(f"Index '{index_name}' already exists")

    except Exception as e:
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            print(f"Creating index '{index_name}'...")
            pc.create_index(
                name=index_name,
                dimension=384,
                metric='euclidean',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            print(f"Index '{index_name}' created successfully")

    model = SentenceTransformer('all-MiniLM-L6-v2')

    company_excel_path = "C:\\JMAN Final Project\\Getting Domains\\company_names_with_URL.xlsx"
    company_data = pd.read_excel(company_excel_path)

    start_row = int(input("Enter start row (0-indexed): "))
    end_row = int(input("Enter end row (exclusive, 0-indexed): "))
    data_to_process = company_data.iloc[start_row:end_row]

    company_names = data_to_process["Company Name"].dropna().str.strip()

    csv_files_directory = "C:\\JMAN Final Project\\Scraping Data\\Scraped Data from websites"
    
    for company_name in company_names:
        cleaned_company_name = clean_company_name(company_name)
        csv_file_name = csv_file_name = os.path.join(csv_files_directory, f"Scraped_data_{cleaned_company_name}.csv")

        try:
            if not os.path.exists(csv_file_name):
                raise FileNotFoundError(
                    f"CSV file for {cleaned_company_name} not found.")

            with open(csv_file_name, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                scraped_data = ""
                for csv_row in reader:
                    scraped_data += " ".join(csv_row)

            translated_data = translate_text(scraped_data)

            chunks = divide_chunks(translated_data)

            for idx, chunk in enumerate(chunks):

                vector_id = generate_vector_id(f"{cleaned_company_name}_{idx}")
                embedding = model.encode(chunk).tolist()
                metadata = {"company_name": cleaned_company_name,
                            "chunk_index": idx, 
                            "original_text": chunk}
                try:
                    print(f"Upserting vector {vector_id} for company {company_name}")
                    index.upsert([(vector_id, embedding, metadata)])
                    print(f"Successfully upserted vector {vector_id}")
                except Exception as e:
                    print(f"Failed to upsert vector {vector_id}: {e}")

        except FileNotFoundError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred for {cleaned_company_name}: {e}")

    print("Embedding process completed.")


if __name__ == "__main__":
    main()
