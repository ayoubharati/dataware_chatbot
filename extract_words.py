import json
import os
import google.generativeai as genai

# --- SETUP CONFIG ---

# Set the path to your schema file (print the directory before running this)
SCHEMA_FILE_PATH = "schema_compact_dataware_test.json"  # <<--- MODIFY THIS AS NEEDED

# Set your Gemini API key
GEMINI_API_KEY = "AIzaSyCh1r6BX-eks-M-Kuj2eHmbm8MQwgfiNTw"  # Replace with your own key

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- LOAD SCHEMA FILE ---
with open(SCHEMA_FILE_PATH, 'r') as f:
    schema = json.load(f)

schema_desc = "\n".join(
    f"{tbl}: {info.get('description','')}"
    for tbl, info in schema.get('tables', {}).items()
)

# --- GEMINI EXTRACTION FUNCTION ---
def extract_search_terms(user_query, schema_desc):
    prompt = f"""
You are a smart NLP assistant.

Extract only the meaningful **data values** from the user query that are useful for querying a data warehouse.

✅ INCLUDE:
- Codes, SKUs, names, brands, amounts, customer types, product types
- Entity names (like customers, departments, pages, devices)
- Identifiers with numbers (like "container 2023", "SKU-789")

❌ EXCLUDE:
- Table names, column names, SQL keywords
- Filler words like "show", "get", "find", etc.
- Dates like "2023", "January", etc. unless they are clearly part of a code or ID (e.g. "order 2023", "report Q1-2023")

Be strict about this: If the date is just a time reference, ignore it.

Schema Description:
{schema_desc}

User Query:
{user_query}

Return only comma-separated values:
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=60,
                temperature=0.1,
                stop_sequences=["\n\n"]
            )
        )
        # Parse CSV into list, strip each value
        return [val.strip() for val in response.text.strip().split(',') if val.strip()]
    except Exception as e:
        print(f"❌ ERROR for query: '{user_query}' → {str(e)}")
        return []
