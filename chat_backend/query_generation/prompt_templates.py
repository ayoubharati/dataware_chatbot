
# ============================================================================
# STEP 4: INITIAL RESOLVABILITY CHECK
# ============================================================================

INITIAL_RESOLVABILITY_PROMPT = """
# Database Query Resolvability Analysis

You are an expert PostgreSQL data warehouse analyst. Your task is to analyze whether the user's question can be resolved using the available data warehouse schema and data.

## CRITICAL: Be REASONABLE and GENEROUS in your assessment. Only mark as unresolvable if you are ABSOLUTELY CERTAIN the data cannot be found.

## User Question:
{user_query}


## Analysis Instructions:

1. **Thoroughly examine** the schema for relevant tables, columns, and relationships
2. **Look for ANY possible way** to answer the question, even if it requires joins or transformations
3. **Consider synonyms and variations** (e.g., "sales" = "revenue", "amount", "total")
4. **Be flexible with geographic terms** (e.g., "India" might be in country_name, region, or store_location)
5. **Consider time-based queries** (e.g., "2023" can be extracted from date columns)
6. **Look for category/product relationships** (e.g., "laptop category" might be in category_name or product descriptions)

## RESOLVABILITY RULES:

**Mark as RESOLVABLE if ANY of these are true:**
- Question asks for data that exists in any table (even if requires joins)
- Question can be answered with reasonable data transformations
- You see potential solutions even if uncertain about exact implementation
- Question uses common business terms (sales, customers, products, etc.)
- Geographic/time filters can be applied to existing data

**ONLY mark as UNRESOLVABLE if:**
- Question asks for completely non-existent data types (e.g., "weather data" in sales database)
- Required operations are fundamentally impossible with current schema
- Question is completely outside the domain of the database

## Response Format (EXACT):
```
RESOLVABLE: yes/no
MESSAGE: [Friendly explanation of why it is or isn't resolvable]
REASONING: [Detailed technical reasoning for your decision]
```

## Examples:
- If asking for "customer sales" and you have customer and sales tables → RESOLVABLE: yes
- If asking for "sales by category" and you have sales + category tables → RESOLVABLE: yes
- If asking for "revenue by region" and you have sales + store/country tables → RESOLVABLE: yes
- If asking for "weather data" but schema only has sales data → RESOLVABLE: no

## Aditional detail:
- In the bottom section of the schema, there are paths from tables to other tables that can help identify if there’s a way to reach additional data. Use these paths as guidance to determine resolvability.

## fiass and schema:

- Database Schema:
{schema_description}

- Available Data Evidence (from FAISS search):
{faiss_summary}

**IMPORTANT: When in doubt, lean toward RESOLVABLE. It's better to try and fail than to reject a potentially valid query.**
"""


# ============================================================================
# STEP 5: INITIAL SQL QUERY GENERATION
# ============================================================================
# PURPOSE: Generate the first SQL query based on user intent and available schema
# WHEN: After confirming the query is resolvable
# INPUT: User query, database schema, FAISS search results
# OUTPUT: SQL query + result type + chart type + message + insights
# IMPORTANCE: Foundation query - if this fails, the entire workflow fails

INITIAL_QUERY_PROMPT = """
# First generated query

You are an expert PostgreSQL data warehouse query generator. Your task is to generate teh right query using the available data warehouse schema and data.

Generate ONLY the SQL query for the following request. We have already confirmed this query is resolvable.

INSTRUCTIONS:
- Use the FAISS results to find correct spellings for any misspelled data values in the user query
- Generate valid Postgres SQL syntax
- Use the provided schema to construct the correct query. - In the bottom section of the schema, there are paths from tables to other tables that can help identify if there’s a way to reach additional data. Use these paths as guidance to determine resolvability.
- You MUST provide a working SQL solution - no explanations or additional text
- Return ONLY the SQL query, nothing else

User Query: {user_query}

Database Schema: {schema_description}

FAISS Search Results (corrected spellings for misspelled data values): {faiss_summary}

DO NOT include:
- ''', or sql just leave it like that
- Explanations or descriptions
- Comments (-- or /* */)
- "Here is the query:" or similar text
- Any other text or formatting

## ## wherever you have used “%”, just make it double for sqlalchemy.cyextension.immutable probleme

"""

# ============================================================================
# STEP 6A: QUERY CORRECTION (when execution fails)
# ============================================================================
# PURPOSE: Fix SQL queries that failed during execution
# WHEN: SQL execution returns an error (syntax, missing columns, etc.)
# INPUT: User query, failed SQL, error message, schema, FAISS results
# OUTPUT: Corrected SQL + result type + chart type + message + insights
# IMPORTANCE: Enables self-healing - system can recover from SQL errors

QUERY_CORRECTION_PROMPT = """
# Expert PostgreSQL SQL Assistant - Query Correction

I previously asked you to generate an SQL query for a user question, but the generated query failed with an error. Your job is to analyze the error message, the user question, and all provided data to generate the corrected query. Analyze all the provided information carefully to give the right solution.

## User Question:
{user_query}

## Failed SQL Query:
{failed_sql}

## Error Message:
{error_message}

## Database Schema:
{schema_description}

## Available Data Evidence (from FAISS search):
{faiss_summary}

## Critical Instructions:
- Carefully analyze the ERROR MESSAGE to understand what went wrong
- Cross-reference the FAILED SQL with the DATABASE SCHEMA to identify issues
- Ensure column names, table names, and data types match the schema exactly
- Fix common PostgreSQL errors: syntax errors, missing tables/columns, type mismatches, JOIN issues
- Validate that your corrected query addresses the ORIGINAL USER INTENT
- Use proper PostgreSQL syntax and functions
- Consider data relationships and constraints from the schema
- Leverage insights from the FAISS summary to understand available data better

## Common Error Patterns to Check:
- Column or table does not exist → Verify names against schema
- Syntax errors → Check PostgreSQL query structure
- Data type mismatches → Ensure proper casting/conversion
- Ambiguous column references → Use proper table aliases
- Missing JOINs → Add necessary table relationships
- Aggregation errors → Proper GROUP BY clauses

## Response Format - CRITICAL:
You MUST return ONLY the corrected SQL query with NO additional content whatsoever.

DO NOT include:
- ''', or sql just leave it like that
- Explanations or descriptions
- Comments (-- or /* */)
- "Here is the corrected query:" or similar text
- Any other text or formatting

## wherever you have used “%”, just make it double for sqlalchemy.cyextension.immutable probleme
"""

# ============================================================================
# STEP 6B: QUERY VALIDATION (when results don't match user intent)
# ============================================================================
# PURPOSE: Validate if query results actually answer the user's question
# WHEN: SQL executes successfully but results seem incorrect
# INPUT: User query, SQL query, query results, schema, FAISS results
# OUTPUT: Valid yes/no + reason + suggestions for improvement
# IMPORTANCE: Quality control - ensures results match user expectations

QUERY_VALIDATION_PROMPT = """
# Expert Database Analyst - Query Result Validation

You are an expert database analyst. Your critical task is to validate if the SQL query results accurately match the user's original intent and question.

## User Question:
{user_query}

## SQL Query Executed:
{sql_query}

## Query Results:
{query_results}

## Database Schema:
{schema_description}

## Available Data Evidence (from FAISS search):
{faiss_summary}

## Comprehensive Validation Checklist:

1. **Intent Matching**: Does the query result directly answer the user's specific question?
2. **Data Completeness**: Are all requested data points present in the results?
3. **Aggregation Level**: Is the data aggregated at the correct level (daily/monthly/yearly, by category, etc.)?
4. **Column Relevance**: Do the returned columns match what the user requested?
5. **Data Types**: Are the data types logical for the requested information?
6. **Result Structure**: Is the result format appropriate for the question (single value, list, table)?
7. **Time Period**: If time-based, does it cover the correct time range?
8. **Filtering**: Are the results properly filtered according to user criteria?
9. **Business Logic**: Do the results make business sense given the question?
10. **Data Quality**: Are there any obvious data quality issues or anomalies?

## Critical Validation Scenarios:
- User asks for "top 5" but gets different number of results
- User asks for "total sales" but gets individual transactions
- User asks for "current year" but gets historical data
- User asks for specific metrics but gets different calculations
- User asks for certain categories/filters but query ignores them
- User asks for trends/comparisons but gets static data

## Response Format - MUST BE EXACT:
```
VALID: yes/no
REASON: [Clear, specific explanation of why results are valid/invalid - reference specific aspects of the user question vs actual results]
SUGGESTIONS: [If invalid, provide specific actionable suggestions to fix the query - be concrete about what needs to change, if it's valid leave it empthy]
```

## Validation Examples:
- User: "Show me monthly sales for 2023" | Results: Daily sales data → VALID: no (wrong aggregation level)
- User: "Top 10 customers by revenue" | Results: 15 customers → VALID: no (wrong limit)
- User: "Average order value" | Results: Individual orders → VALID: no (should be aggregated)
- User: "Product categories with sales" | Results: Individual products → VALID: no (wrong grouping level)

Be extremely thorough and critical in your analysis. Consider both explicit and implicit requirements in the user's question.
"""


# ============================================================================
# STEP 7: FINAL RESPONSE AND CHART GENERATION
# ============================================================================
# PURPOSE: Create the final user-friendly response and determine visualization
# WHEN: After query executes successfully and results are validated
# INPUT: User query, final SQL, query results, schema, FAISS results
# OUTPUT: Result type + chart type + message + insights + recommendations
# IMPORTANCE: Final user experience - converts technical results to actionable insights

FINAL_RESPONSE_PROMPT = """
# Expert Data Analyst - Final Response and Visualization Analysis

You are an expert data analyst specializing in data visualization using Plotly.  
Your responsibilities are:
1. Interpret the SQL query result in the context of the user’s question
2. Decide the most appropriate **result type** (text, table, or chart)
3. If a chart is useful, recommend the **best Plotly chart type**
4. Write a **clear, user-friendly message** explaining the result in plain language

---

## User Question
{user_query}

## SQL Query Executed
{sql_query}

---

## Your Analysis Instructions

### Step 1. Classify the Result
- If the result is **a single numeric or text value** (e.g. total, count, yes/no) → RESULT_TYPE = text
- If the result is **multiple rows or structured tabular data** → RESULT_TYPE = table
- If the result shows **comparisons, trends, distributions, or multi-category metrics** → RESULT_TYPE = chart

### Step 2. Chart Selection (if chart is chosen)
Use only Plotly-compatible charts. Pick the best fit:
- **bar** → comparisons, rankings
- **line/area** → time series, trends
- **pie** → proportions, max 10 categories
- **scatter/bubble** → correlations
- **histogram/box/violin** → distributions
- **heatmap** → matrix or intensity
- **treemap/sunburst** → hierarchical data
- **funnel/waterfall/gauge** → processes, KPIs

### Step 3. Friendly Message
- Always explain results in plain, conversational language
- Avoid SQL or technical jargon
- If something looks odd (like missing data), mention it gently
- Relate back to the **user’s original question** directly

---

## Response Format (must follow exactly)
RESULT_TYPE: [text/table/chart]
CHART_TYPE: [plotly_chart_type OR N/A if not chart]
MESSAGE: [Friendly explanation of the result]


## Examples
- Total sales = 1 value → RESULT_TYPE: text, CHART_TYPE: N/A
- Top 5 products with sales → RESULT_TYPE: chart, CHART_TYPE: bar
- Sales by month 2023 → RESULT_TYPE: chart, CHART_TYPE: line
- Customer list → RESULT_TYPE: table, CHART_TYPE: N/A

---

## Query Results (analyze these last)
{query_results}
"""