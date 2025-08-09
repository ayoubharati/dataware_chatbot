import json
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
    """Compose a compact but rich prompt for Gemini to synthesize a final query and explanations."""

    def fmt_hit(hit: Dict[str, Any]) -> str:
        return f"(score={hit['similarity_score']}, table={hit['table']}, row={hit['row_preview']})"

    lines: List[str] = []
    lines.append("You are a senior data assistant that maps user intent to a structured data request.")
    lines.append("Your goals:")
    lines.append("1) Normalize/correct data values in the user's query using FAISS evidence.")
    lines.append("2) Propose a final database-friendly query (natural language or SQL-like filter spec).")
    lines.append("3) For each result item provided, identify what it represents, explain why it matches, and where it lives (table and likely columns).")
    lines.append("")

    if schema_description:
        lines.append("Schema summary (for context):")
        lines.append(schema_description.strip())
        lines.append("")

    lines.append(f"Original user query: {user_query}")
    lines.append(f"Extracted candidate data values: {extracted_terms}")
    lines.append("")

    lines.append("FAISS evidence per term (top 10 each):")
    for term, hits in per_term_hits.items():
        lines.append(f"- Term: {term}")
        for h in hits[:10]:
            lines.append(f"  • {fmt_hit(h)}")
    lines.append("")

    lines.append("FAISS evidence for the whole query (top 10):")
    for h in whole_query_hits[:10]:
        lines.append(f"- {fmt_hit(h)}")
    lines.append("")

    lines.append("Instructions:")
    lines.append("- Correct misspellings or partial values by selecting the best-supported canonical value from FAISS evidence.")
    lines.append("- Suggest where each canonical value maps in the database as table.column when inferable from row previews.")
    lines.append("- If multiple tables are plausible, list the options ranked by likelihood.")
    lines.append("- Keep the final query precise and executable (e.g., SQL WHERE clauses or a JSON filter object).")
    lines.append("- Include a concise explanation for each result item (10 per term + 10 for whole query) in the output.")
    lines.append("")

    lines.append("Output JSON with this structure:")
    lines.append("{")
    lines.append("  \"final_terms\": [ { \"original\": str, \"canonical\": str, \"reason\": str, \"locations\": [\"table.col\"] } ],")
    lines.append("  \"final_query\": { \"type\": \"SQL\"|\"NL\"|\"FILTER\", \"query\": str },")
    lines.append("  \"results_explanation\": {")
    lines.append("    \"per_term\": { term: [ { \"table\": str, \"score\": float, \"why\": str } ] },")
    lines.append("    \"whole_query\": [ { \"table\": str, \"score\": float, \"why\": str } ]")
    lines.append("  }")
    lines.append("}")

    return "\n".join(lines)


def orchestrate_query(user_query: str,
                      per_term_k: int = 10,
                      whole_query_k: int = 10,
                      call_gemini: bool = True) -> Dict[str, Any]:
    """End-to-end flow: extract terms, run FAISS per-term and for full query, and optionally call Gemini."""

    # 1) Extract candidate data values (not table/column names)
    extracted_terms = extract_search_terms(user_query, schema_desc) or []

    # 2) Build FAISS engine and run searches
    engine = MultiTableEmbeddingSearch()
    engine.load_all_embeddings()

    per_term_hits: Dict[str, List[Dict[str, Any]]] = {}
    for term in extracted_terms:
        per_term_hits[term] = _run_faiss(engine, term, per_term_k)

    whole_query_hits = _run_faiss(engine, user_query, whole_query_k)

    # 3) Build prompt for Gemini
    prompt = build_gemini_prompt(
        user_query=user_query,
        extracted_terms=extracted_terms,
        per_term_hits=per_term_hits,
        whole_query_hits=whole_query_hits,
        schema_description=schema_desc,
    )

    result: Dict[str, Any] = {
        'user_query': user_query,
        'extracted_terms': extracted_terms,
        'per_term_hits': per_term_hits,
        'whole_query_hits': whole_query_hits,
        'gemini_prompt': prompt,
    }

    # 4) Call Gemini to produce the final query + explanations
    if call_gemini:
        try:
            resp = model.generate_content(prompt)
            result['gemini_output_text'] = getattr(resp, 'text', None)
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

    return result


def run_complete_analysis(user_query: str):
    """Complete analysis workflow as requested"""
    print(f"🔍 Analyzing query: '{user_query}'")
    print("=" * 60)

    # Run the complete orchestration
    result = orchestrate_query(user_query, per_term_k=10, whole_query_k=10, call_gemini=True)

    print(f"📝 Extracted terms: {result['extracted_terms']}")
    print()

    # Show per-term FAISS results (10 each)
    print("🔎 FAISS Results per extracted term (top 10 each):")
    for term, hits in result['per_term_hits'].items():
        print(f"\n  Term: '{term}'")
        for i, hit in enumerate(hits[:10], 1):
            print(f"    {i}. Table: {hit['table']} | Score: {hit['similarity_score']} | {hit['row_preview']}")

    # Show whole query FAISS results (10 total)
    print(f"\n🔎 FAISS Results for whole query (top 10):")
    for i, hit in enumerate(result['whole_query_hits'][:10], 1):
        print(f"  {i}. Table: {hit['table']} | Score: {hit['similarity_score']} | {hit['row_preview']}")

    print("\n" + "=" * 60)
    print("🤖 GEMINI FINAL ANALYSIS:")
    print("=" * 60)

    if 'gemini_output_text' in result:
        print(result['gemini_output_text'])
    elif 'gemini_error' in result:
        print(f"❌ Gemini Error: {result['gemini_error']}")
    else:
        print("❌ No Gemini output received")

    if 'gemini_output_json' in result:
        print("\n📋 Parsed JSON Output:")
        print(json.dumps(result['gemini_output_json'], indent=2))

    return result


if __name__ == '__main__':
    # Test with a sample query
    test_query = "show me facbok marketing campaigns"
    result = run_complete_analysis(test_query)

    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print(f"- Extracted {len(result['extracted_terms'])} terms")
    print(f"- Found {sum(len(hits) for hits in result['per_term_hits'].values())} per-term results")
    print(f"- Found {len(result['whole_query_hits'])} whole-query results")
    print(f"- Gemini analysis: {'✅ Success' if 'gemini_output_text' in result else '❌ Failed'}")

