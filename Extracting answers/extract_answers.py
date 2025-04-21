import os
import time
import pandas as pd
import google.generativeai as genai # type: ignore

from dotenv import load_dotenv # type: ignore
from pinecone import Pinecone, ServerlessSpec # type: ignore
from sentence_transformers import SentenceTransformer # type: ignore


current_key_index = 0
api_key_usage = {}
GEMINI_API_KEYS = []


def init_pinecone(api_key, environment, index_name):

    pc = Pinecone(api_key=api_key, environment=environment)
    
    try:
        index = pc.Index(index_name)
        print(f"Index '{index_name}' already exists")
        return index

    except Exception as e:
        print("Pinecone index not found")
        raise


def init_api_keys():

    global GEMINI_API_KEYS, api_key_usage
    GEMINI_API_KEYS = [
        os.getenv("GEMINI_API_KEY1"),
        os.getenv("GEMINI_API_KEY2")
    ]
    GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]  # Remove empty
    api_key_usage = {key: 0 for key in GEMINI_API_KEYS}
    print(f"Initialized {len(GEMINI_API_KEYS)} API keys")


def rotate_gemini_key():

    global current_key_index
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    print(f"Rotated to API key index {current_key_index}")


def get_current_gemini_key():

    global api_key_usage
    current_key = GEMINI_API_KEYS[current_key_index]
    if api_key_usage[current_key] >= 1300:
        rotate_gemini_key()
        current_key = GEMINI_API_KEYS[current_key_index]
    api_key_usage[current_key] += 1
    return current_key


def init_gemini():
    try:
        genai.configure(api_key=get_current_gemini_key())
        model = genai.GenerativeModel("gemini-2.0-flash")
        print(f"Initialized with key index {current_key_index}")
        return model
    except Exception as e:
        print(f"Failed: {e}. Rotating key...")
        rotate_gemini_key()
        return init_gemini()


def clean_company_name(company_name):
    company_name = company_name.replace("/", "-")
    company_name = company_name.replace(" ", "_")
    return company_name


def load_input_data(input_excel_path):
    try:
        input_dataframe = pd.read_excel(input_excel_path)
        print(f"Loaded input data with {len(input_dataframe)} companies")

        start_row = int(input("Enter the start row (0-based index): "))
        end_row = int(input("Enter the end row (exclusive, 0-based index): "))

        input_data_to_process = input_dataframe.iloc[start_row:end_row]
        return input_data_to_process

    except Exception as e:
        print(f"Failed to load input data: {e}")
        raise


def load_or_create_output_data(output_excel_path, questions):
    if os.path.exists(output_excel_path):
        try:
            output_dataframe = pd.read_excel(output_excel_path)
            print(
                f"Loaded existing output data with {len(output_dataframe)} entries")
            return output_dataframe
        except Exception as e:
            print(f"Failed to load existing output data: {e}")
            columns = ["Company Name", "Official Website URL"] + questions
            output_dataframe = pd.DataFrame(columns=columns)
            print("Created new output dataframe")
            return output_dataframe
    else:
        columns = ["Company Name", "Official Website URL"] + questions
        output_dataframe = pd.DataFrame(columns=columns)
        print("Created new output dataframe")
        return output_dataframe


def save_output_data(output_data, output_excel_path):
    try:
        output_data.to_excel(output_excel_path, index=False)
        print(f"Saved output data to {output_excel_path}")
    except Exception as e:
        print(f"Failed to save output data: {e}")


def get_query_embedding(question):
    model = SentenceTransformer('all-MiniLM-L6-v2')

    embedding = model.encode(question)
    return embedding.tolist()


def query_pinecone(index, company_name, question, query_embedding, top_k=3):
    try:
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            filter={"company_name": clean_company_name(company_name)},
            include_metadata=True
        )

        matches = results.get("matches", [])
        print(
            f"Found {len(matches)} matches in Pinecone for company: {company_name} and for question: {question}")

        if matches:
            print(matches)
        return matches

    except Exception as e:
        print(f"Error querying Pinecone for {company_name}: {e}")
        return []


def query_gemini(model, question, context):
    try:
        prompt = f"""
        Based EXACTLY on the following information about a company, please answer this question:
        
        Question: {question}
        
        Company Information:
        {context}
        
        Rules:
        1. Answer ONLY using the provided information
        2. Be concise (7 words max)
        3. If the information is not available, respond with "Not Found"
        4. Never make up information
        """

        response = model.generate_content(prompt)
        answer = response.text.strip()

        if not answer:
            return "Not Found"

        return answer

    except Exception as e:
        print(f"Error querying Gemini: {e}")
        return "Not Found"


def check_company_status(output_data, company_name, questions):
    company_mask = output_data["Company Name"] == company_name

    if not company_mask.any():
        return {
            "exists": False,
            "message": "Company not found in output data. Will process it."
        }

    company_row = output_data[company_mask].iloc[0]
    unanswered_questions = []

    for question in questions:
        if company_row[question] == "Not Found":
            unanswered_questions.append(question)

    if not unanswered_questions:
        return {
            "exists": True,
            "all_answered": True,
            "message": "All the required details have been obtained already."
        }
    else:
        return {
            "exists": True,
            "all_answered": False,
            "unanswered": unanswered_questions,
            "message": f"Company exists but {len(unanswered_questions)} questions remain unanswered."
        }


def update_output_with_results(output_data, results, questions):
    company_name = results["Company Name"]

    company_mask = output_data["Company Name"] == company_name

    if company_mask.any():
        for question in questions:
            if results[question] != "Not Found":
                output_data.loc[company_mask, question] = results[question]
    else:
        output_data = pd.concat(
            [output_data, pd.DataFrame([results])], ignore_index=True)

    return output_data


def process_company(company_name, website_url, index, questions):
    print(f"Processing company: {company_name}")

    results = {}
    results["Company Name"] = company_name
    results["Official Website URL"] = website_url

    for question in questions:
        query_embedding = get_query_embedding(question)

        matches = query_pinecone(
            index, company_name, question, query_embedding)

        if not matches:
            results[question] = "Not Found"
            continue

        context = "\n\n".join([match.get("metadata", {}).get(
            "original_text", "") for match in matches])

        current_model = init_gemini()
        answer = query_gemini(current_model, question, context)
        results[question] = answer

        time.sleep(5)

    return results


def process_all_companies(input_data, output_data, index, questions, output_excel_path):
    total_companies = len(input_data)
    print(f"Starting to process {total_companies} companies")

    for idx, row in input_data.iterrows():
        company_name = row["Company Name"]
        website_url = row["official website URL"]

        print(f"Processing {idx+1}/{total_companies}: {company_name}")

        status = check_company_status(output_data, company_name, questions)
        print(status["message"])

        if status["exists"] and status["all_answered"]:
            continue

        results = process_company(company_name, website_url, index, questions)

        output_data = update_output_with_results(
            output_data, results, questions)

        save_output_data(output_data, output_excel_path)

        time.sleep(1)

    print("Finished processing all companies")
    return output_data


if __name__ == "__main__":

    load_dotenv()

    init_api_keys()

    input_excel_path = "C:\\JMAN Final Project\\Getting Domains\\company_names_with_URL.xlsx"
    output_excel_path = "C:\\JMAN Final Project\\details_of_companies.xlsx"

    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
    pinecone_index_name = "translated-embeddings"
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    questions = [
        "What does this company do? (1-2 sentence description)",
        "What software or technology does this company specialize in?",
        "What industry or sector does this company belong to?",
        "Does the company mention any notable clients or partners?",

        "What is the company's approximate employee headcount?",
        "Does the company have a known parent company or subsidiaries?",
        "Are there any known investors or funding sources for this company?",
        "What is the company's approximate annual revenue?",
        "In which geographical regions does this company operate?",

        "What is the company's full physical address?",
        "What is the company's contact email address",
        "What is the company's phone number?"
    ]

    index = init_pinecone(
        pinecone_api_key, pinecone_environment, pinecone_index_name)

    input_data = load_input_data(input_excel_path)
    output_data = load_or_create_output_data(output_excel_path, questions)

    output_data = process_all_companies(
        input_data, output_data, index, questions, output_excel_path)
