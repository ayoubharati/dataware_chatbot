import json
import time
from typing import List, Dict, Any

# Import all necessary modules
import google.generativeai as genai
from extract_words import extract_search_terms, schema_desc
from search_using_fiass import MultiTableEmbeddingSearch

# Hardcoded Gemini API key
GEMINI_API_KEY = "AIzaSyCh1r6BX-eks-M-Kuj2eHmbm8MQwgfiNTw"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Global FAISS engine - initialized once for all users
_global_faiss_engine = None

def get_global_faiss_engine():
    """Get or initialize the global FAISS engine (singleton pattern)"""
    global _global_faiss_engine
    if _global_faiss_engine is None:
        print("🚀 Initializing global FAISS engine (one-time setup)...")
        _global_faiss_engine = MultiTableEmbeddingSearch()
        _global_faiss_engine.load_all_embeddings()
        print("✅ Global FAISS engine ready for all users!")
    return _global_faiss_engine


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


def build_gemini_prompt(user_query: str,
                        extracted_terms: List[str],
                        per_term_hits: Dict[str, List[Dict[str, Any]]],
                        whole_query_hits: List[Dict[str, Any]],
                        schema_description: str = "") -> str:
    """Compose a comprehensive prompt for Gemini to generate the final query and explanations."""

    def fmt_hit(hit: Dict[str, Any]) -> str:
        # Simplified format to reduce tokens
        return f"{hit['table']}:{hit['row_preview'][:60]}"

    lines: List[str] = []
    lines.append("You are a data assistant. Generate a database query from user intent.")
    lines.append("")
    lines.append("Schema:")
    lines.append(schema_description.strip())
    lines.append("")
    lines.append(f"Query: {user_query}")
    lines.append(f"Terms: {extracted_terms}")
    lines.append("")

    # Simplified FAISS evidence - only top 3 results per term to reduce tokens
    lines.append("Evidence per term (top 3):")
    for term, hits in per_term_hits.items():
        lines.append(f"{term}:")
        for h in hits[:3]:  # Reduced from 10 to 3
            lines.append(f"  {fmt_hit(h)}")
    lines.append("")

    # Simplified whole query evidence - only top 5
    lines.append("Whole query evidence (top 5):")
    for h in whole_query_hits[:5]:  # Reduced from 10 to 5
        lines.append(f"  {fmt_hit(h)}")
    lines.append("")

    lines.append("Output JSON:")
    lines.append("{")
    lines.append("  \"final_terms\": [ { \"original\": str, \"canonical\": str, \"locations\": [\"table.col\"] } ],")
    lines.append("  \"final_query\": { \"type\": \"SQL\"|\"NL\"|\"FILTER\", \"query\": str }")
    lines.append("}")

    return "\n".join(lines)


def orchestrate_query(user_query: str,
                      per_term_k: int = 10,
                      whole_query_k: int = 10,
                      call_gemini: bool = True) -> Dict[str, Any]:
    """End-to-end flow: extract terms, run FAISS per-term and for full query, and optionally call Gemini."""
    
    performance_metrics = {}

    # 1) Extract candidate data values (not table/column names)
    print("🔄 Extracting search terms (Gemini #1)...")
    start_time = time.time()
    extracted_terms = extract_search_terms(user_query, schema_desc) or []
    term_extraction_time = time.time() - start_time
    performance_metrics['term_extraction'] = term_extraction_time
    print(f"   ✅ Terms extracted: {extracted_terms} ({term_extraction_time:.3f}s)")

    # 2) Get global FAISS engine (already initialized)
    print("🔍 Getting FAISS engine...")
    start_time = time.time()
    engine = get_global_faiss_engine()
    faiss_setup_time = time.time() - start_time
    performance_metrics['faiss_setup'] = faiss_setup_time
    print(f"   ✅ FAISS ready ({faiss_setup_time:.3f}s)")

    print("🔍 Running per-term FAISS searches...")
    start_time = time.time()
    per_term_hits: Dict[str, List[Dict[str, Any]]] = {}
    for term in extracted_terms:
        term_start = time.time()
        per_term_hits[term] = _run_faiss(engine, term, per_term_k)
        term_time = time.time() - term_start
        print(f"   🔍 FAISS search '{term}': {len(per_term_hits[term])} results ({term_time:.3f}s)")

    per_term_search_time = time.time() - start_time
    performance_metrics['per_term_search'] = per_term_search_time

    print("🔍 Running whole query FAISS search...")
    start_time = time.time()
    whole_query_hits = _run_faiss(engine, user_query, whole_query_k)
    whole_query_search_time = time.time() - start_time
    performance_metrics['whole_query_search'] = whole_query_search_time
    print(f"   ✅ FAISS whole query: {len(whole_query_hits)} results ({whole_query_search_time:.3f}s)")

    # 3) Build prompt for Gemini
    print("📝 Building Gemini prompt...")
    start_time = time.time()
    prompt = build_gemini_prompt(
        user_query=user_query,
        extracted_terms=extracted_terms,
        per_term_hits=per_term_hits,
        whole_query_hits=whole_query_hits,
        schema_description=schema_desc,
    )
    prompt_build_time = time.time() - start_time
    performance_metrics['prompt_build'] = prompt_build_time
    
    # Count tokens (approximate)
    prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
    performance_metrics['prompt_tokens'] = int(prompt_tokens)
    print(f"   ✅ Prompt built ({prompt_build_time:.3f}s, ~{int(prompt_tokens)} tokens)")

    result: Dict[str, Any] = {
        'user_query': user_query,
        'extracted_terms': extracted_terms,
        'per_term_hits': per_term_hits,
        'whole_query_hits': whole_query_hits,
        'gemini_prompt': prompt,
        'performance_metrics': performance_metrics,
    }

    # 4) Call Gemini to produce the final query + explanations
    if call_gemini:
        print("🤖 Calling Gemini (Gemini #2)...")
        start_time = time.time()
        try:
            resp = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,  # Reduced from default
                    temperature=0.1,        # Lower temperature for faster, more focused responses
                    stop_sequences=["\n\n"] # Stop on double newline
                )
            )
            gemini_time = time.time() - start_time
            performance_metrics['gemini_call'] = gemini_time
            
            result['gemini_output_text'] = getattr(resp, 'text', None)
            
            # Try to get token usage if available
            try:
                if hasattr(resp, 'usage_metadata'):
                    usage = resp.usage_metadata
                    if hasattr(usage, 'prompt_token_count'):
                        performance_metrics['gemini_prompt_tokens'] = usage.prompt_token_count
                    if hasattr(usage, 'candidates_token_count'):
                        performance_metrics['gemini_response_tokens'] = usage.candidates_token_count
                        total_tokens = usage.prompt_token_count + usage.candidates_token_count
                        performance_metrics['gemini_total_tokens'] = total_tokens
                        print(f"   ✅ Gemini response ({gemini_time:.3f}s, {total_tokens} tokens)")
                    else:
                        print(f"   ✅ Gemini response ({gemini_time:.3f}s)")
                else:
                    print(f"   ✅ Gemini response ({gemini_time:.3f}s)")
            except Exception:
                print(f"   ✅ Gemini response ({gemini_time:.3f}s)")
            
            # Try to parse JSON from the response, if present
            try:
                # Try to locate a JSON block in the text
                text = result.get('gemini_output_text') or ''
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    result['gemini_output_json'] = json.loads(text[start:end+1])
            except Exception:
                pass
        except Exception as e:
            result['gemini_error'] = str(e)
            print(f"   ❌ Gemini error: {str(e)}")

    return result


def run_complete_analysis(user_query: str):
    """Complete analysis workflow as requested"""
    start_time = time.time()

    # Run the complete orchestration
    result = orchestrate_query(user_query, per_term_k=10, whole_query_k=10, call_gemini=True)

    execution_time = time.time() - start_time
    
    # Show performance summary
    print("\n" + "="*50)
    print("📊 PERFORMANCE SUMMARY")
    print("="*50)
    
    if 'performance_metrics' in result:
        metrics = result['performance_metrics']
        print(f"🤖 Gemini #1 (Terms):    {metrics.get('term_extraction', 0):.3f}s")
        print(f"🔍 FAISS Setup:          {metrics.get('faiss_setup', 0):.3f}s")
        print(f"🔍 FAISS Per-term:       {metrics.get('per_term_search', 0):.3f}s")
        print(f"🔍 FAISS Whole Query:    {metrics.get('whole_query_search', 0):.3f}s")
        print(f"📝 Prompt Build:         {metrics.get('prompt_build', 0):.3f}s")
        print(f"🤖 Gemini #2 (Query):    {metrics.get('gemini_call', 0):.3f}s")
        print(f"⏱️  Total Execution:      {execution_time:.3f}s")
        
        # Token usage
        if 'gemini_total_tokens' in metrics:
            print(f"🔤 Total Tokens:        {metrics['gemini_total_tokens']}")
            print(f"   ├─ Prompt:           {metrics.get('gemini_prompt_tokens', 0)}")
            print(f"   └─ Response:         {metrics.get('gemini_response_tokens', 0)}")
        elif 'prompt_tokens' in metrics:
            print(f"🔤 Estimated Tokens:    ~{metrics['prompt_tokens']}")
    
    print("="*50)
    
    # Show only the final query
    if 'gemini_output_json' in result:
        final_query = result['gemini_output_json'].get('final_query', {}).get('query', 'N/A')
        print(f"Query: {final_query}")
    else:
        print("Query: Failed to generate")

    return result


def initialize_app():
    """Initialize the application - call this at startup"""
    print("🚀 Initializing DataWare Chatbot Application...")
    
    # Pre-initialize FAISS engine
    faiss_engine = get_global_faiss_engine()
    
    print("✅ Application ready!")
    return faiss_engine

if __name__ == '__main__':
    # Initialize the app first
    initialize_app()
    
    # Test with a sample query
    test_query = "show me facbok marketing campaigns"
    result = run_complete_analysis(test_query)
