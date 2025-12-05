import os
import google.generativeai as genai

SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema_dataware_test.md")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

with open(SCHEMA_FILE_PATH, "r", encoding="utf-8") as f:
    schema_str = f.read()

# --- GEMINI EXTRACTION FUNCTION ---
def extract_search_terms(user_query, schema_str):
    prompt = f"""
You are analyzing a user query to identify terms that need EMBEDDING SEARCH correction in a database.

User Query: {user_query}

CONTEXT:
- User queries may contain misspelled data values that exist in the database
- Common English word misspellings (like "totl" for "total") don't need embedding search - the query generator LLM will understand them
- We need to find ACTUAL DATA VALUES that might be misspelled and need to be matched against the database content

IDENTIFY TERMS THAT NEED EMBEDDING SEARCH:
✅ Product names/models that might be misspelled (e.g., "laptps" → "Laptops")
✅ Brand names with unusual spelling (e.g., "samung" → "Samsung") 
✅ Country/location names that might be abbreviated/misspelled (e.g., "inda" → "India", "usa" → "United States")
✅ Specific identifiers/codes (e.g., "st01", "SKU789", "ORDER123")
✅ Category values that might be misspelled but are NOT column/table names
✅ Any term that looks like it could be actual database content but is unclear/misspelled

DON'T EXTRACT:
❌ Common English words even if misspelled ("totl", "amout", "chrt") - query generator will understand
❌ SQL/database terms ("select", "table", "join", "show", "find")
❌ Chart/analysis terms ("bar", "chart", "graph", "report")
❌ Time references ("2023", "year", "month") unless they're part of specific IDs
❌ Generic terms ("all", "data", "information")
❌ Column names or table names from the schema (even if misspelled like "departmnt" for "department")
❌ Database structure terms that appear in the schema

FOR EACH TERM THAT NEEDS SEARCH:
Create a 2-3 word contextual phrase that:
- Includes the original term exactly as written
- Adds 1-2 relevant context words from the same domain
- Keeps the meaning focused and specific
- Uses context from the database schema when possible

EXAMPLES:
User: "Show total sales amount by Laptops category in India for 2023"
Analysis: "Laptops" is a product category that might need verification, "India" is a country that could be misspelled
Output: Laptops category, India country

User: "find me in which station the container st01 exist"  
Analysis: "st01" is clearly a specific identifier, "station" is context
Output: station st01

User: "show sales for samung phones in electronics departmnt"
Analysis: "samung" (Samsung misspelled) is a brand name, "departmnt" is a column/table name so exclude it
Output: samung phones

TASK:
Analyze the user query and return ONLY the contextual phrases that need embedding search.
Return as comma-separated phrases with no extra text.

OUTPUT FORMAT (STRICT):
- Return ONLY the contextual phrases separated by commas.
- No explanations, no extra text, no quotes, no bullet points, no line breaks.
- Example: Laptops category, India country

DATABASE SCHEMA:
{schema_str}

Contextual phrases needing embedding search:
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=80,
                temperature=0.1,
                stop_sequences=["\n\n", "\n"]
            )
        )
        
        result = response.text.strip()
        if not result or result.lower() in ['none', 'no terms', 'nothing']:
            return []
            
        return [phrase.strip() for phrase in result.split(',') if phrase.strip()]
        
    except Exception as e:
        print(f"❌ ERROR for query: '{user_query}' → {str(e)}")
        return []
