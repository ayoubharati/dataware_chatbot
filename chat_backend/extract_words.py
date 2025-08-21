import os
import google.generativeai as genai

# --- SETUP CONFIG ---
SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema_dataware_test.md")
GEMINI_API_KEY = "AIzaSyD3hsAiQaxccROpqCBGKLK6NwIGeyNR35w"  # Replace with your own key

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- LOAD SCHEMA FILE ---
with open(SCHEMA_FILE_PATH, 'r', encoding='utf-8') as f:
    schema_str = f.read()

# --- GEMINI EXTRACTION FUNCTION ---
def extract_search_terms(user_query, schema_str):
    prompt = f"""
You are an extraction tool.

TASK:
From the user query, extract only the exact text values that are relevant for identifying entities or parameters in a data warehouse search.

STRICT RULES:
1. Copy the text exactly as it appears in the query.
2. Do not fix spelling, grammar, or wording.
3. Do not change capitalization or punctuation.
4. Do not add, remove, or infer any words.
5. If a value is repeated, include it only once.
6. Return only comma-separated values, no extra text, no quotes, no explanation.
7. If any extracted value contains multiple words, split them and return each word individually.

INCLUDE:
- Codes, SKUs, names, brands, amounts, customer types, product types.
- Entity names (customers, departments, devices, regions, etc.).
- Identifiers with numbers (like "order 2023", "SKU-789").

EXCLUDE:
- Table names, column names, SQL keywords.
- Generic filler words ("show", "find", "get").
- Dates or time references unless part of an ID/code.

Database Schema (for context only, do not alter output based on it):
{schema_str}

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
        return [val.strip() for val in response.text.strip().split(',') if val.strip()]
    except Exception as e:
        print(f"❌ ERROR for query: '{user_query}' → {str(e)}")
        return []

# Example usage
terms = extract_search_terms("show me all sales from Nike shoes in region north", schema_str)
print(terms)
