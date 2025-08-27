from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import re
import os
from typing import List, Dict, Any, Optional
import logging
import pandas as pd
from sqlalchemy import create_engine
import google.generativeai as genai
from extract_words import extract_search_terms
from search_using_fiass import MultiTableEmbeddingSearch
from chart_generator import generate_plotly_chart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema_dataware_test.md")
GEMINI_API_KEY = "AIzaSyAOnTwL8D2EtUzXJyppjpiPVATOgAMf0YE"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'dataware_test',
    'user': 'postgres',
    'password': 'bath123'
}

# Initialize components
DATABASE_URL = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Load schema
try:
    with open(SCHEMA_FILE_PATH, 'r', encoding='utf-8') as f:
        schema_desc = f.read()
    logger.info(f"✅ Schema loaded from {SCHEMA_FILE_PATH}")
except Exception as e:
    logger.error(f"❌ Failed to load schema: {e}")
    schema_desc = ""

# Global FAISS engine
_global_faiss_engine = None

def get_global_faiss_engine():
    """Get or initialize the global FAISS engine (singleton pattern)"""
    global _global_faiss_engine
    if _global_faiss_engine is None:
        try:
            logger.info("🚀 Initializing global FAISS engine...")
            _global_faiss_engine = MultiTableEmbeddingSearch()
            _global_faiss_engine.load_all_embeddings()
            logger.info("✅ Global FAISS engine ready!")
        except Exception as e:
            logger.error(f"❌ FAISS initialization failed: {e}")
            return None
    return _global_faiss_engine

def log_gemini_prompt_to_file(prompt: str, user_query: str, prompt_type: str = "QUERY"):
    """Log the final Gemini prompt to a text file for debugging"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Create debug_logs directory if it doesn't exist
        debug_dir = os.path.join(os.path.dirname(__file__), "debug_logs")
        os.makedirs(debug_dir, exist_ok=True)

        filename = os.path.join(debug_dir, f"gemini_prompt_{prompt_type}_{timestamp}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== GEMINI PROMPT LOG ({prompt_type}) ===\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"User Query: {user_query}\n")
            f.write(f"Prompt Type: {prompt_type}\n")
            f.write(f"{'='*50}\n")
            f.write(f"FINAL PROMPT SENT TO GEMINI:\n")
            f.write(f"{'='*50}\n")
            f.write(prompt)
            f.write(f"\n{'='*50}\n")
        logger.info(f"📝 Gemini prompt logged to: {filename}")
    except Exception as e:
        logger.error(f"Failed to log Gemini prompt: {e}")

def log_chart_result_to_file(chart_data: Dict[str, Any], user_query: str, sql_query: str, retry_info: Dict[str, Any] = None):
    """Log chart result data to a JSON file for debugging"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Create debug_logs directory if it doesn't exist
        debug_dir = os.path.join(os.path.dirname(__file__), "debug_logs")
        os.makedirs(debug_dir, exist_ok=True)

        filename = os.path.join(debug_dir, f"chart_result_{timestamp}.json")

        log_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "user_query": user_query,
            "sql_query": sql_query,
            "chart_result": chart_data,
            "retry_info": retry_info or {}
        }

        with open(filename, 'w', encoding='utf-8') as f:
            # Import json locally to avoid global import issues
            import json
            json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📊 Chart result logged to: {filename}")
    except Exception as e:
        logger.error(f"Failed to log chart result: {e}")

def _flatten_row_preview(row: Dict[str, Any], max_items: int = 8, max_val_len: int = 80) -> str:
    """Create a short, human-readable preview string for a DB row."""
    parts = []
    for i, (k, v) in enumerate(row.items()):
        if i >= max_items:
            parts.append("…")
            break
        s = str(v)
        if len(s) > max_val_len:
            s = s[: max_val_len - 1] + "…"
        parts.append(f"{k}={s}")
    return ", ".join(parts)

def _run_faiss(engine: MultiTableEmbeddingSearch, text: str, k: int = 10) -> List[Dict[str, Any]]:
    """FAISS search that returns structured results including table name and row preview."""
    # Ensure embeddings and index are ready
    if engine.index is None:
        engine.load_all_embeddings()

    query_emb = engine.model.encode([text]).astype('float32')
    distances, indices = engine.index.search(query_emb, k)

    out: List[Dict[str, Any]] = []
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(engine.metadata):
            meta = engine.metadata[idx]
            table = meta.get('table_name')
            row = meta.get('row_data', {})
            score = 1 / (1 + float(dist))
            out.append({
                'table': table,
                'similarity_score': round(score, 4),
                'row': row,
                'row_preview': _flatten_row_preview(row)
            })
    return out

def run_sql(sql_query: str, preview_limit: int = 10000) -> Dict[str, Any]:
    """Run SQL via pandas/SQLAlchemy. Returns dict with df and preview."""
    try:
        logger.info(f"Executing SQL: {sql_query}")
        df = pd.read_sql_query(sql_query, db_engine)
        cols = list(df.columns)
        row_count = len(df)
        preview = df.head(min(preview_limit, row_count)).to_dict(orient="records")
        return {"success": True, "df": df, "columns": cols, "row_count": row_count, "preview": preview}
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return {"success": False, "error": str(e), "df": pd.DataFrame(), "columns": [], "row_count": 0, "preview": []}

def infer_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    numerics = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    datetimes = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c]) or "date" in c.lower() or "time" in c.lower()]
    categoricals = [c for c in df.columns if c not in numerics and c not in datetimes]
    return {"numeric": numerics, "datetime": datetimes, "categorical": categoricals}

def choose_chart_type(df: pd.DataFrame) -> str:
    if df.empty or df.shape[1] == 0:
        return "table"
    t = infer_column_types(df)
    if len(t["datetime"]) >= 1 and len(t["numeric"]) >= 1:
        return "line"
    if len(t["categorical"]) >= 1 and len(t["numeric"]) >= 1:
        return "bar"
    if len(t["numeric"]) >= 2:
        return "scatter"
    if len(t["categorical"]) >= 1:
        return "pie"
    return "table"

def aggregate_or_sample(df: pd.DataFrame, chart_type: str, max_points: int = 500) -> pd.DataFrame:
    if len(df) <= max_points:
        return df
    t = infer_column_types(df)
    if chart_type == "bar" and t["categorical"] and t["numeric"]:
        x, y = t["categorical"][0], t["numeric"][0]
        agg = df.groupby(x, dropna=False, as_index=False)[y].sum()
        return agg.sort_values(y, ascending=False).head(min(50, len(agg)))
    if chart_type == "line" and t["datetime"] and t["numeric"]:
        x, y = t["datetime"][0], t["numeric"][0]
        tmp = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(tmp[x]):
            with pd.option_context("mode.chained_assignment", None):
                tmp[x] = pd.to_datetime(tmp[x], errors="coerce")
        tmp = tmp.dropna(subset=[x]).sort_values(x)
        if len(tmp) > max_points:
            idx = (pd.Series(range(len(tmp))) * (len(tmp) / max_points)).astype(int).clip(0, len(tmp) - 1)
            tmp = tmp.iloc[sorted(set(idx.tolist()))]
        return tmp[[x, y]]
    if chart_type == "scatter" and len(t["numeric"]) >= 2:
        x, y = t["numeric"][:2]
        return df[[x, y]].sample(n=min(max_points, len(df)), random_state=42)
    return df.sample(n=min(max_points, len(df)), random_state=42)

def build_plotly_visualization(df: pd.DataFrame, force_type: Optional[str] = None) -> Dict[str, Any]:
    """Build Plotly chart specification instead of simple config"""
    if df.empty:
        return {
            "type": "empty",
            "plotly_json": {
                "data": [],
                "layout": {"title": "No data found"},
                "config": {"displayModeBar": False}
            }
        }
    
    # Determine chart type
    chart_type = force_type or choose_chart_type(df)
    
    # Infer column types for config
    t = infer_column_types(df)
    config = {
        "title": "Query Result",
        "columns": list(df.columns),
        "rowCount": len(df)
    }
    
    # Set up config based on chart type
    if chart_type == "bar" and t["categorical"] and t["numeric"]:
        config["xKey"] = t["categorical"][0]
        config["yKeys"] = t["numeric"][:3]
    elif chart_type == "line" and t["datetime"] and t["numeric"]:
        config["xKey"] = t["datetime"][0]
        config["yKeys"] = t["numeric"][:3]
    elif chart_type == "pie" and t["categorical"] and t["numeric"]:
        config["nameKey"] = t["categorical"][0]
        config["valueKey"] = t["numeric"][0]
    elif chart_type == "scatter" and len(t["numeric"]) >= 2:
        config["xKey"] = t["numeric"][0]
        config["yKey"] = t["numeric"][1]
    
    # Generate the complete Plotly specification
    plotly_spec = generate_plotly_chart(df, chart_type, config)
    
    return {
        "type": "chart",
        "chart_type": chart_type,
        "plotly_json": plotly_spec
    }
    
def save_gemini_response(response_text: str, user_query: str):
    """Simple function to save Gemini response to txt file"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        debug_dir = os.path.join(os.path.dirname(__file__), "debug_logs")
        os.makedirs(debug_dir, exist_ok=True)
        
        filename = os.path.join(debug_dir, f"gemini_response_{timestamp}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Query: {user_query}\n")
            f.write(f"Response:\n{response_text}")
        
        logger.info(f"Response saved to: {filename}")
    except Exception as e:
        logger.error(f"Failed to save response: {e}")

def build_retry_gemini_prompt(
    user_query: str,
    failed_sql: str,
    error_message: str,
    schema_description: str,
    extracted_terms: List[str],
    per_term_hits: Dict[str, List[Dict[str, Any]]],
    whole_query_hits: List[Dict[str, Any]]
) -> str:
    """Build a retry prompt when SQL execution fails"""
    def fmt_hit(hit: Dict[str, Any]) -> str:
        return f"{hit.get('table')} :: {hit.get('row_preview', '')[:80]}"

    per_term_lines = []
    for term, hits in per_term_hits.items():
        per_term_lines.append(f"- **{term}:**")
        for h in hits[:5]:  # Fewer hits for retry to keep prompt shorter
            per_term_lines.append(f"  - {fmt_hit(h)}")

    whole_lines = [f"  - {fmt_hit(h)}" for h in whole_query_hits[:5]]

    prompt = f"""
# Expert Postgres SQL Assistant - Query Correction

You are an expert Postgres SQL assistant for business analytics. A previous SQL query failed with an error. Please analyze the error and generate a corrected query that fully addresses the user's original intent.

## CRITICAL Response Format

Your response MUST follow this EXACT format with NO deviations:

RESOLVABLE: yes/no
MESSAGE: [MANDATORY user-friendly explanation - must NOT mention any errors or problems]
SQL: [Corrected PostgreSQL query only if resolvable=yes]
RESULT_TYPE: [text/chart only if resolvable=yes]
CHART_TYPE: [bar/line/pie/scatter/table only if resolvable=yes and result_type=chart]
INSIGHTS: [Optional bullet points]

## Important Guidelines

- **MESSAGE field must sound completely normal** - never mention that there was a previous error or retry attempt
- Write the MESSAGE as if this is the first successful response to the user's query
- Use friendly, conversational language that directly answers what the user asked
- For chart results, write an introductory message explaining what you'll show them
- **If the result would be complex tabular data that cannot be visualized as a simple chart or reduced to a single text value, set RESOLVABLE to "no" and explain that this type of content cannot be represented in our current interface**
- **After generating the corrected query, verify it:**
  - Follows the user's original intent completely
  - Uses only valid table and column names from the schema
  - Has correct syntax and proper joins
  - Uses appropriate data types and functions

## Context for Correction

### Failed Query (for your reference only):
```sql
{failed_sql}

ERROR MESSAGE:
{error_message}

ORIGINAL USER QUERY:
{user_query}

Database Schema:
{schema_description}

FAISS Evidence:
Per-term:
{chr(10).join(per_term_lines)}

Whole-query:
{chr(10).join(whole_lines)}

Please fix the SQL query by:
1. Checking table and column names against the provided schema
2. Fixing syntax errors from the original query
3. Ensuring proper joins and relationships between tables
4. Correcting data types and functions to match schema specifications
5. Verifying the corrected query fully addresses the user's original request

Remember: The MESSAGE you provide to the user must sound completely natural and should never mention that there was a previous error or correction attempt.
""".strip()
    return prompt


def parse_structured_gemini(text: str) -> Dict[str, str]:
    """Parse the new structured Gemini response format with improved SQL extraction"""
    try:
        s = text.replace("\r\n", "\n").strip()
        
        # Initialize result with defaults
        result = {
            "resolvable": "no",
            "message": "",
            "sql": "",
            "result_type": "",
            "chart_type": "none",
            "insights": ""
        }
        
        # Extract each field individually with more precise patterns
        
        # Extract RESOLVABLE
        resolvable_match = re.search(r"RESOLVABLE:\s*(yes|no)", s, re.IGNORECASE)
        if resolvable_match:
            result["resolvable"] = resolvable_match.group(1).strip().lower()
        
        # Extract MESSAGE (everything between MESSAGE: and SQL: or next field)
        message_match = re.search(r"MESSAGE:\s*(.*?)(?=\s*(?:SQL:|RESULT_TYPE:|CHART_TYPE:|INSIGHTS:|$))", s, re.IGNORECASE | re.DOTALL)
        if message_match:
            result["message"] = message_match.group(1).strip()
        
        # Extract SQL (everything between SQL: and RESULT_TYPE: or next field)
        sql_match = re.search(r"SQL:\s*(.*?)(?=\s*(?:RESULT_TYPE:|CHART_TYPE:|INSIGHTS:|$))", s, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql_raw = sql_match.group(1).strip()
            # Clean SQL - remove markdown code blocks and extra formatting
            sql_raw = re.sub(r"^```(?:sql)?", "", sql_raw, flags=re.IGNORECASE | re.MULTILINE)
            sql_raw = re.sub(r"```$", "", sql_raw, flags=re.MULTILINE)
            # Remove any trailing structured format fields that might have leaked in
            sql_raw = re.sub(r"\s*(?:RESULT_TYPE|CHART_TYPE|INSIGHTS):.*$", "", sql_raw, flags=re.IGNORECASE | re.DOTALL)
            result["sql"] = sql_raw.strip()
        
        # Extract RESULT_TYPE
        result_type_match = re.search(r"RESULT_TYPE:\s*(text|chart)", s, re.IGNORECASE)
        if result_type_match:
            result["result_type"] = result_type_match.group(1).strip().lower()
        
        # Extract CHART_TYPE
        chart_type_match = re.search(r"CHART_TYPE:\s*(\w+)", s, re.IGNORECASE)
        if chart_type_match:
            result["chart_type"] = chart_type_match.group(1).strip().lower()
        
        # Extract INSIGHTS (everything after INSIGHTS:)
        insights_match = re.search(r"INSIGHTS:\s*(.*?)$", s, re.IGNORECASE | re.DOTALL)
        if insights_match:
            result["insights"] = insights_match.group(1).strip()
        
        # Validation and defaults for resolvable queries
        if result["resolvable"] == "yes":
            if not result["result_type"]:
                result["result_type"] = "text"
            if result["result_type"] == "chart" and result["chart_type"] == "none":
                result["chart_type"] = "table"
        
        # Debug logging
        logger.info(f"Parsed Gemini response:")
        logger.info(f"  - Resolvable: {result['resolvable']}")
        logger.info(f"  - Message: {result['message'][:100]}...")
        logger.info(f"  - SQL: {result['sql'][:100]}...")
        logger.info(f"  - Result Type: {result['result_type']}")
        logger.info(f"  - Chart Type: {result['chart_type']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing Gemini response: {e}")
        logger.error(f"Raw text: {text}")
        return {
            "resolvable": "no",
            "message": text.strip() if text else "Unable to process query",
            "sql": "",
            "result_type": "",
            "chart_type": "none",
            "insights": ""
        }
        
def build_improved_gemini_prompt(
    user_query: str,
    extracted_terms: List[str],
    per_term_hits: Dict[str, List[Dict[str, Any]]],
    whole_query_hits: List[Dict[str, Any]],
    schema_description: Any = "",
) -> str:
    """Build structured prompt with mandatory MESSAGE field and explicit requirements"""
    def fmt_hit(hit: Dict[str, Any]) -> str:
        return f"{hit.get('table')} :: {hit.get('row_preview', '')[:80]}"

    per_term_lines = []
    for term, hits in per_term_hits.items():
        per_term_lines.append(f"- {term}:")
        for h in hits[:10]:
            per_term_lines.append(f"  • {fmt_hit(h)}")

    whole_lines = [f"  • {fmt_hit(h)}" for h in whole_query_hits[:10]]
    schema_str = str(schema_description)

    prompt = f"""
# Expert Postgres SQL Assistant for Business Analytics

You are an expert Postgres SQL assistant for business analytics. First determine if the user query can be answered with the available schema and data evidence.

## CRITICAL Response Format

Your response MUST follow this EXACT format with NO deviations:

RESOLVABLE: yes/no
MESSAGE: [MANDATORY user-facing explanation/reason - always provide this]
SQL: [PostgreSQL query ONLY if resolvable=yes]
RESULT_TYPE: [text/chart ONLY if resolvable=yes - REQUIRED for yes cases]
CHART_TYPE: [bar/line/pie/scatter/table ONLY if resolvable=yes and result_type=chart - REQUIRED for chart cases]
INSIGHTS: [bullet points ONLY if resolvable=yes]

## Decision Logic

- **RESOLVABLE=yes:** Query can be answered using available tables/columns from schema AND FAISS evidence shows relevant data AND result can be displayed as either:
  - A single text value (number, string, date, etc.)
  - A chart visualization (bar, line, pie, scatter, or simple table)
- **RESOLVABLE=no:** Query asks for data not in schema, requires external information, FAISS shows no relevant matches, OR the result would be complex tabular data that cannot be meaningfully visualized

## For RESOLVABLE=yes (ALL fields mandatory)

- **MESSAGE:** Write a friendly, human explanation (2–4 sentences) in plain language. Avoid naming internal table/column identifiers; use business terms (e.g., "sales", "customers", "date"). For chart results, write a simple introductory message explaining what you're about to show.
- **SQL:** Valid PostgreSQL query using only schema tables/columns
- **RESULT_TYPE:** "text" for single values/simple results, "chart" for aggregated/visual data
- **CHART_TYPE:** Best chart type (bar=categories+numbers, line=time+numbers, pie=parts of whole, scatter=correlation, table=fallback for complex data)
- **INSIGHTS:** 3-5 bullet points of expected findings (OPTIONAL — prefer embedding insights into MESSAGE itself).

## For RESOLVABLE=no

- **MESSAGE:** Polite explanation of why query cannot be answered. Common reasons:
  - "This type of content cannot be represented in our current interface" (for complex tabular results)
  - "I don't have access to that data in the available database"
  - "This query requires external information that isn't available"
- All other fields must be omitted/empty

## Important Notes

- **Complex tabular data** (like detailed reports, lists with many columns, or raw data dumps) should be marked as RESOLVABLE=no
- Only mark as resolvable if the result can be meaningfully displayed as a single value or a clear visualization
- The MESSAGE field is ALWAYS required and must be user-facing text regardless of resolvability

## Database Schema
{schema_str}

## User Query
{user_query}

## FAISS Evidence

### Per-term:
{chr(10).join(per_term_lines)}

### Whole-query:
{chr(10).join(whole_lines)}

**Be precise about resolvability.** If schema lacks needed tables/columns, FAISS shows no relevant data, or the result would be complex tabular data that can't be visualized, answer no.
""".strip()
    return prompt

def orchestrate_improved_query(
    user_query: str,
    per_term_k: int = 10,
    whole_query_k: int = 10,
    call_gemini: bool = True,
) -> Dict[str, Any]:
    metrics = {}

    # Extract terms
    t0 = time.time()
    try:
        terms = extract_search_terms(user_query, schema_desc) or []
    except Exception as e:
        logger.warning(f"extract_search_terms failed: {e}")
        terms = []
    metrics["term_extraction"] = time.time() - t0

    # FAISS evidence
    t0 = time.time()
    per_hits: Dict[str, List[Dict[str, Any]]] = {}
    whole_hits: List[Dict[str, Any]] = []
    engine = get_global_faiss_engine()
    if engine:
        for term in terms:
            per_hits[term] = _run_faiss(engine, term, per_term_k)
        whole_hits = _run_faiss(engine, user_query, whole_query_k)
    metrics["faiss"] = time.time() - t0

    prompt = build_improved_gemini_prompt(
        user_query=user_query,
        extracted_terms=terms,
        per_term_hits=per_hits,
        whole_query_hits=whole_hits,
        schema_description=schema_desc,
    )

    result: Dict[str, Any] = {
        "user_query": user_query,
        "extracted_terms": terms,
        "per_term_hits": per_hits,
        "whole_query_hits": whole_hits,
        "gemini_prompt": prompt,
        "performance_metrics": metrics,
    }

    if not call_gemini:
        return result

    t0 = time.time()
    try:
        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=800, temperature=0.2, top_p=0.9),
        )
        metrics["gemini_call"] = time.time() - t0
        text = getattr(resp, "text", "") or ""
        save_gemini_response(text, user_query)
        result["gemini_output_text"] = text
        
        # Parse the structured response and add parsed fields directly
        parsed = parse_structured_gemini(text)
        result.update(parsed)
        
    except Exception as e:
        result["gemini_error"] = str(e)
        result["resolvable"] = "no"
        result["message"] = f"Error processing query: {str(e)}"
        logger.error(f"Gemini error: {e}")

    return result

def retry_failed_query(
    user_query: str,
    failed_sql: str,
    error_message: str,
    extracted_terms: List[str],
    per_term_hits: Dict[str, List[Dict[str, Any]]],
    whole_query_hits: List[Dict[str, Any]],
    schema_description: str
) -> Dict[str, Any]:
    """Retry a failed SQL query by asking Gemini to fix it"""
    logger.info(f"🔄 Retrying failed query: {user_query}")
    logger.info(f"❌ Original error: {error_message}")

    retry_prompt = build_retry_gemini_prompt(
        user_query=user_query,
        failed_sql=failed_sql,
        error_message=error_message,
        schema_description=schema_description,
        extracted_terms=extracted_terms,
        per_term_hits=per_term_hits,
        whole_query_hits=whole_query_hits
    )

    try:
        resp = model.generate_content(
            retry_prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=800, temperature=0.1, top_p=0.9),
        )
        text = getattr(resp, "text", "") or ""
        save_gemini_response(text, user_query)

        # Parse the structured response
        parsed = parse_structured_gemini(text)

        result = {
            "user_query": user_query,
            "retry_attempt": True,
            "original_sql": failed_sql,
            "original_error": error_message,
            "gemini_retry_output": text,
        }
        result.update(parsed)

        return result

    except Exception as e:
        logger.error(f"Retry attempt failed: {e}")
        return {
            "resolvable": "no",
            "message": "I couldn't resolve this problem. Please try rephrasing your question or asking for something different.",
            "retry_attempt": True,
            "original_sql": failed_sql,
            "original_error": error_message,
        }

def initialize_app():
    """Initialize the application - call this at startup"""
    logger.info("🚀 Initializing Improved DataWare Chatbot Application...")
    faiss_engine = get_global_faiss_engine()
    logger.info("✅ Improved application ready!")
    return faiss_engine

# Flask Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Improved DataWare Chatbot Backend is running',
        'timestamp': time.time()
    })

@app.route('/query', methods=['POST'])
def process_query():
    """Main endpoint to process user queries with structured flow"""
    try:
        # Get JSON data from request
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing query in request body',
                'status': 'error'
            }), 400

        user_query = data['query'].strip()

        if not user_query:
            return jsonify({
                'error': 'Empty query provided',
                'status': 'error'
            }), 400

        # Optional parameters
        per_term_k = data.get('per_term_k', 10)
        whole_query_k = data.get('whole_query_k', 10)
        call_gemini = data.get('call_gemini', True)

        logger.info(f"Processing structured query: {user_query}")

        # Process the query
        start_time = time.time()
        result = orchestrate_improved_query(
            user_query=user_query,
            per_term_k=per_term_k,
            whole_query_k=whole_query_k,
            call_gemini=call_gemini
        )

        total_execution_time = time.time() - start_time
        result['total_execution_time'] = total_execution_time

        # Check if query is resolvable
        is_resolvable = result.get('resolvable', 'no') == 'yes'
        message = result.get('message', 'Unable to process query')
        
        logger.info(f"Query resolvability: {is_resolvable}")
        
        # Log metrics
        if 'performance_metrics' in result:
            metrics = result['performance_metrics']
            logger.info(f"Resolvability check completed in {total_execution_time:.3f}s")
            logger.info(f"  - Term extraction: {metrics.get('term_extraction', 0):.3f}s")
            logger.info(f"  - FAISS searches: {metrics.get('faiss', 0):.3f}s")
            logger.info(f"  - Gemini call: {metrics.get('gemini_call', 0):.3f}s")

        if not is_resolvable:
            # Query not resolvable - return immediately
            return jsonify({
                'resolvable': False,
                'message': message,
                'result': None,
                'insights': [],
                'execution_time': round(total_execution_time, 3)
            })

        # Query is resolvable - execute SQL
        sql_query = result.get('sql', '').strip()
        result_type = result.get('result_type', '').lower()
        chart_type = result.get('chart_type', 'none').lower()
        insights_text = result.get('insights', '')
        
        # Parse insights into list - simplified
        insights = [line.strip() for line in insights_text.split('\n') if line.strip()] if insights_text else []

        if not sql_query:
            logger.error("Resolvable query but no SQL generated")
            return jsonify({
                'resolvable': False,
                'message': 'Unable to generate SQL query',
                'result': None,
                'insights': []
            })

        # Execute SQL
        t0 = time.time()
        sql_result = run_sql(sql_query)
        sql_execution_time = time.time() - t0

        if not sql_result['success']:
            logger.error(f"SQL execution failed: {sql_result.get('error')}")

            # Attempt to retry with Gemini to fix the SQL
            logger.info("🔄 Attempting to retry with corrected SQL...")
            retry_result = retry_failed_query(
                user_query=user_query,
                failed_sql=sql_query,
                error_message=sql_result.get('error', 'Unknown error'),
                extracted_terms=result.get('extracted_terms', []),
                per_term_hits=result.get('per_term_hits', {}),
                whole_query_hits=result.get('whole_query_hits', []),
                schema_description=schema_desc
            )

            # Check if retry was successful
            if retry_result.get('resolvable', 'no') == 'yes' and retry_result.get('sql'):
                corrected_sql = retry_result.get('sql', '').strip()
                logger.info(f"🔧 Trying corrected SQL: {corrected_sql}")

                # Execute the corrected SQL
                t0_retry = time.time()
                retry_sql_result = run_sql(corrected_sql)
                retry_sql_execution_time = time.time() - t0_retry

                if retry_sql_result['success']:
                    logger.info(f"✅ Retry successful! Executed in {retry_sql_execution_time:.3f}s, returned {retry_sql_result['row_count']} rows")
                    # Use the corrected results
                    sql_result = retry_sql_result
                    sql_execution_time = retry_sql_execution_time
                    original_sql_query = sql_query  # Store original for metadata
                    sql_query = corrected_sql  # Update for response metadata
                    message = retry_result.get('message', message)
                    result_type = retry_result.get('result_type', result_type)
                    chart_type = retry_result.get('chart_type', chart_type)

                    # Add retry metadata to result for response
                    result['retry_attempted'] = True
                    result['original_sql'] = original_sql_query
                    result['corrected_sql'] = corrected_sql
                else:
                    logger.error(f"❌ Retry also failed: {retry_sql_result.get('error')}")
                    return jsonify({
                        'resolvable': False,
                        'message': f'Query failed even after correction attempt. Original error: {sql_result.get("error", "Unknown error")}. Retry error: {retry_sql_result.get("error", "Unknown error")}',
                        'result': None,
                        'insights': [],
                        'retry_attempted': True,
                        'original_sql': sql_query,
                        'corrected_sql': corrected_sql
                    })
            else:
                # Retry failed to generate a valid query
                return jsonify({
                    'resolvable': False,
                    'message': f'Query generated but execution failed: {sql_result.get("error", "Unknown error")}. Unable to automatically correct the query.',
                    'result': None,
                    'insights': [],
                    'retry_attempted': True,
                    'original_sql': sql_query
                })

        logger.info(f"SQL executed successfully in {sql_execution_time:.3f}s, returned {sql_result['row_count']} rows")

        # Process result based on type - trust Gemini's classification first
        if result_type == 'text' or (not result_type and sql_result['row_count'] == 1 and len(sql_result['columns']) == 1):
            # Single scalar value result
            if sql_result['row_count'] > 0:
                only_col = sql_result['columns'][0]
                scalar_value = sql_result['preview'][0].get(only_col)
                value = '' if scalar_value is None else str(scalar_value)
            else:
                value = 'No data found'
            
            result_data = {
                'type': 'text',
                'value': value
            }
            logger.info(f"Text result: {value}")

            # Log text result for debugging (optional, mainly for charts but keeping consistency)
            retry_info = {}
            if result.get('retry_attempted'):
                retry_info = {
                    'retry_attempted': True,
                    'original_sql': result.get('original_sql', ''),
                    'corrected_sql': result.get('corrected_sql', '')
                }

            log_chart_result_to_file(
                chart_data=result_data,
                user_query=user_query,
                sql_query=sql_query,
                retry_info=retry_info
            )
            
        # Replace this section in your chart result handling:
        else:
            # Chart/visual result
            df = sql_result['df']
            valid_chart_types = ['bar', 'line', 'pie', 'scatter', 'table']
            force_chart_type = chart_type if chart_type in valid_chart_types else None
            
            # Use the new Plotly generation
            vis_spec = build_plotly_visualization(df, force_type=force_chart_type)
            
            result_data = {
                'type': 'chart',
                'chart_type': vis_spec['chart_type'],
                'plotly_json': vis_spec['plotly_json']  # Complete Plotly spec
            }
            logger.info(f"Chart result: {vis_spec['chart_type']} with Plotly spec generated")
        # Prepare response data
        response_data = {
            'resolvable': True,
            'message': message,
            'result': result_data,
            'insights': insights,
            'execution_time': round(total_execution_time, 3),
            'sql_execution_time': round(sql_execution_time, 3),
            'sql_query': sql_query,
            'query_metadata': {
                'result_type': result_type,
                'chart_type': chart_type,
                'row_count': sql_result.get('row_count', 0),
                'columns': sql_result.get('columns', [])
            }
        }

        # Add retry information if applicable
        if result.get('retry_attempted'):
            response_data['retry_attempted'] = True
            response_data['original_sql'] = result.get('original_sql', '')
            response_data['corrected_sql'] = result.get('corrected_sql', '')

        # Return final response
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'resolvable': False,
            'message': f'Sorry, I encountered an error: {str(e)}',
            'result': None,
            'insights': []
        }), 500

@app.errorhandler(404)
def not_found(_):
    return jsonify({'error': 'Endpoint not found', 'status': 'error'}), 404

@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({'error': 'Method not allowed', 'status': 'error'}), 405

if __name__ == '__main__':
    # Initialize the app first
    initialize_app()

    # Debug: Print all registered routes
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint} ({', '.join(rule.methods)})")

    # Start Flask server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )