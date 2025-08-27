# Query Generation System

A modular, AI-powered system for generating SQL queries from natural language using Google Gemini, with integrated FAISS search, query validation, and chart generation capabilities.

## 🎯 **What This System Does**

This system transforms natural language questions into working SQL queries through a sophisticated 7-step workflow:

1. **Schema Loading** - Loads your existing database schema
2. **Contextual Term Extraction** - Extracts meaningful phrases (not single words) for better FAISS search
3. **FAISS Vector Search** - Finds relevant data using your existing FAISS setup
4. **Initial Resolvability Check** - Deep analysis to determine if the question can be answered
5. **SQL Query Generation** - Creates SQL using Gemini with rich context
6. **Query Testing & Validation** - Executes and validates results with automatic retry logic
7. **Final Response & Chart Generation** - Creates user-friendly responses and chart data

## 🏗️ **Architecture Overview**

The system is designed as a **smart wrapper** around your existing working components:

- **`extract_words.py`** → `term_extractor.py` (wrapper)
- **`search_using_fiass.py`** → `faiss_search.py` (wrapper) 
- **`schema_dataware_test.md`** → `schema_manager.py` (wrapper)

**No rebuilding of existing functionality** - just intelligent orchestration and enhancement.

## 📁 **File Structure**

```
query_generation/
├── config.py              # Configuration & API keys
├── schema_manager.py      # Loads your existing schema_dataware_test.md
├── term_extractor.py      # Wraps your existing extract_words.py
├── faiss_search.py        # Wraps your existing search_using_fiass.py
├── gemini_client.py       # Handles all Gemini API calls
├── query_tester.py        # Tests SQL execution & validation
├── query_orchestrator.py  # Orchestrates the entire workflow
├── main.py               # Demo script for the complete workflow
├── requirements.txt       # Dependencies
└── README.md             # This documentation
```

## 🚀 **Key Features**

### **Contextual Phrase Extraction**
- **No more single words!** Extracts meaningful phrases (2-4 words) for better FAISS performance
- Uses your existing `extract_words.py` with enhanced prompts
- Examples: "customer registrations", "Australia", "by year" instead of just "customer", "Australia", "year"

### **Smart Resolvability Checking**
- **Initial deep analysis** before generating SQL to avoid wasting resources
- Thoroughly evaluates if the question aligns with available schema and data
- Only proceeds if the question can be meaningfully answered

### **Intelligent Query Generation**
- Uses Gemini with rich context: schema + FAISS results + user intent
- Generates SQL that's optimized for your specific database structure
- Includes result type classification (chart/text/table)

### **Robust Testing & Validation**
- **Automatic execution testing** with error correction
- **Result validation** using Gemini to ensure output matches user intent
- **Retry logic** for failed queries with intelligent correction

### **Chart-Ready Output**
- **Final Gemini call** generates user-friendly responses and chart data
- **Chart.js compatible JSON** for frontend rendering
- **Fallback to text responses** when data isn't suitable for visualization

## 🔄 **Complete Workflow**

### **Step 1: Schema Loading**
```python
# Loads your existing schema_dataware_test.md
schema_description = schema_manager.get_combined_schema_description()
```

### **Step 2: Term Extraction**
```python
# Uses your existing extract_words.py with enhanced prompts
extracted_terms = term_extractor.extract_terms_with_fallback(
    user_query, schema_description
)
# Returns: ['customer registrations', 'Australia', 'by year']
```

### **Step 3: FAISS Search**
```python
# Uses your existing search_using_fiass.py
per_term_results = faiss_search.search_multiple_terms(extracted_terms, 10)
whole_query_results = faiss_search.search_whole_query(user_query, 10)
```

### **Step 4: Resolvability Check**
```python
# Deep analysis to determine if question can be answered
resolvability_result = gemini_client.check_initial_resolvability(
    user_query, schema_description, faiss_summary
)
# Early exit if question cannot be resolved
```

### **Step 5: SQL Generation**
```python
# Generate SQL with rich context
gemini_result = gemini_client.generate_initial_query(
    user_query, schema_description, faiss_summary
)
# Returns structured response with SQL, result type, chart type
```

### **Step 6: Testing & Validation**
```python
# Execute and validate with retry logic
while retry_count <= max_retries:
    # Test execution
    execution_result = query_tester.test_query_execution(sql_query)
    
    if execution_result["success"]:
        # Validate results match user intent
        validation_result = gemini_client.validate_query_results(...)
        if validation_result["valid"]:
            break  # Success!
        else:
            # Refine query based on validation feedback
            sql_query = refine_query(...)
    else:
        # Correct failed query
        sql_query = correct_query(...)
```

### **Step 7: Final Response & Chart**
```python
# Generate user-friendly response and chart data
final_result = gemini_client.generate_final_response_and_chart(
    user_query, final_sql, query_results, schema_description, faiss_summary
)
# Returns: friendly message + chart JSON or text response
```

## 🛠️ **Setup & Installation**

### **Prerequisites**
- Python 3.8+
- Your existing working components:
  - `extract_words.py` (with contextual phrase extraction)
  - `search_using_fiass.py` (with FAISS index and metadata)
  - `schema_dataware_test.md` (database schema)
  - PostgreSQL database connection

### **Installation**
1. **Activate your virtual environment:**
   ```bash
   cd chat_backend
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\Activate.ps1  # Windows
   ```

2. **Install dependencies:**
   ```bash
   cd query_generation
   pip install -r requirements.txt
   ```

3. **Verify configuration in `config.py`:**
   - Database connection details
   - Gemini API key
   - File paths

## 🧪 **Testing the System**

### **Run the Complete Workflow Demo**
```bash
cd chat_backend/query_generation
python main.py
```

This will run the complete 7-step workflow with the example query:
> "Make a bar chart of customer registrations in Australia by year"

### **Expected Output**
```
🚀 COMPLETE QUERY GENERATION WORKFLOW
============================================================
User Query: Make a bar chart of customer registrations in Australia by year
============================================================

📋 Step 1: load_schema
   Status: ✅ Success
   Duration: 0.004s

📋 Step 2: extract_terms
   Status: ✅ Success
   Duration: 1.700s
   Extracted Terms: ['customer registrations', 'Australia', 'by year']

📋 Step 3: faiss_search
   Status: ✅ Success
   Duration: 0.227s
   FAISS Searches: Completed

📋 Step 4: check_resolvability
   Status: ✅ Success
   Duration: 2.100s
   Resolvable: yes
   Message: This query can be answered using customer registration data...

📋 Step 5: generate_initial_query
   Status: ✅ Success
   Duration: 3.259s
   Generated SQL: SELECT EXTRACT(YEAR FROM registration_date)...

📋 Step 6: test_and_validate
   Status: ✅ Success
   Duration: 4.132s
   ✅ Final SQL Query: [Working SQL]
   📊 Query Results: 4 rows returned
   🔍 Validation: yes

📋 Step 7: generate_final_response
   Status: ✅ Success
   Duration: 2.800s
   ✅ Final Response Generated
   💬 Message: Based on your question, here's what we found...
   📊 Chart Data: bar chart
   Chart JSON: {"type": "bar", "data": {...}}

🏁 Final Status: ✅ SUCCESS

🎯 FINAL OUTPUT:
Message: Based on your question, here's what we found...
Chart Type: bar
Chart Data: Available for frontend rendering

⏱️ Total Workflow Time: 13.622s
```

## 📊 **Output Formats**

### **Successful Query Response**
```json
{
  "resolvable": true,
  "friendly_message": "Based on your question, here's what we found...",
  "query": "SELECT EXTRACT(YEAR FROM registration_date)...",
  "chart_json": {
    "type": "bar",
    "data": {
      "labels": ["2020", "2021", "2022", "2023"],
      "datasets": [{
        "label": "Customer Registrations",
        "data": [15, 23, 18, 12],
        "backgroundColor": "rgba(54, 162, 235, 0.8)"
      }]
    },
    "options": {
      "title": "Customer Registrations in Australia by Year",
      "xAxis": "Year",
      "yAxis": "Number of Registrations"
    }
  }
}
```

### **Unresolvable Query Response**
```json
{
  "resolvable": false,
  "message": "I'm sorry, but I don't have access to weather data in the current database...",
  "reasoning": "The schema only contains sales and customer data, not weather information..."
}
```

## 🔧 **Configuration**

### **Database Configuration**
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'dataware_test',
    'user': 'postgres',
    'password': 'bath123'
}
```

### **Gemini Configuration**
```python
GEMINI_API_KEY = "your_api_key_here"
GEMINI_MODEL = 'gemini-1.5-flash'
GEMINI_CONFIG = {
    'max_output_tokens': 800,
    'temperature': 0.2,
    'top_p': 0.9
}
```

### **FAISS Configuration**
```python
FAISS_PER_TERM_K = 10      # Results per search term
FAISS_WHOLE_QUERY_K = 10   # Results for whole query search
```

### **Retry Configuration**
```python
MAX_RETRY_ATTEMPTS = 3     # Maximum query correction attempts
RETRY_TEMPERATURE = 0.1    # Lower temperature for corrections
```

## 🎨 **Chart Generation**

### **Supported Chart Types**
- **Bar Charts** - Categories with numeric values
- **Line Charts** - Time series data
- **Pie Charts** - Parts of a whole
- **Scatter Plots** - Correlation analysis
- **Tables** - Fallback for complex data

### **Chart.js Compatibility**
The system generates Chart.js compatible JSON that can be directly used in frontend applications:

```javascript
// Frontend usage example
const chartData = response.chart_json;
new Chart(ctx, {
    type: chartData.type,
    data: chartData.data,
    options: chartData.options
});
```

## 🚨 **Error Handling**

### **Resolvability Errors**
- Early exit if question cannot be answered
- Friendly error messages explaining why
- No wasted resources on unresolvable queries

### **Query Execution Errors**
- Automatic SQL correction using Gemini
- Retry logic with intelligent error analysis
- Fallback strategies for common issues

### **Validation Errors**
- Result validation using Gemini
- Query refinement based on feedback
- Continuous improvement until success

## 🔍 **Debugging & Logging**

### **Comprehensive Logging**
- Step-by-step execution tracking
- Performance metrics for each step
- Detailed error information

### **Result Persistence**
- Workflow results saved to JSON files
- Timestamped for easy tracking
- Complete audit trail of all operations

### **Gemini Prompt Logging**
- All prompts logged for debugging
- Response parsing validation
- Easy troubleshooting of AI interactions

## 🔗 **Integration with Existing Systems**

### **Frontend Integration**
The system is designed to work seamlessly with your existing frontend:

```python
# Example: Flask endpoint integration
@app.route('/query', methods=['POST'])
def process_query():
    user_query = request.json['query']
    
    orchestrator = QueryOrchestrator()
    result = orchestrator.generate_query_workflow(user_query)
    
    if result['success']:
        final_result = result['final_result']
        return jsonify({
            'resolvable': True,
            'message': final_result['friendly_message'],
            'chart_data': final_result.get('chart_json'),
            'text_response': final_result.get('text_response'),
            'sql_query': final_result['query']
        })
    else:
        return jsonify({
            'resolvable': False,
            'message': final_result['message']
        })
```

### **Database Integration**
- Uses your existing PostgreSQL connection
- Compatible with your current schema
- No database changes required

## 📈 **Performance Characteristics**

### **Typical Execution Times**
- **Schema Loading**: ~0.005s
- **Term Extraction**: ~1.5-2.0s (Gemini API call)
- **FAISS Search**: ~0.2-0.5s
- **Resolvability Check**: ~2.0-3.0s (Gemini API call)
- **SQL Generation**: ~3.0-4.0s (Gemini API call)
- **Testing & Validation**: ~4.0-6.0s (including retries)
- **Final Response**: ~2.5-3.5s (Gemini API call)

**Total Workflow**: ~13-20 seconds for complex queries

### **Optimization Features**
- Early exit for unresolvable queries
- Efficient FAISS search with existing indexes
- Smart retry logic to minimize API calls
- Result caching and reuse where possible

## 🚀 **Advanced Usage**

### **Custom Prompts**
You can customize Gemini prompts by modifying the methods in `gemini_client.py`:

```python
def _build_custom_prompt(self, user_query: str, **kwargs):
    # Your custom prompt logic here
    return custom_prompt
```

### **Extended Validation**
Add custom validation logic in the orchestrator:

```python
def _custom_validation(self, results, context):
    # Your custom validation logic
    return validation_result
```

### **Custom Chart Types**
Extend chart generation for your specific needs:

```python
def generate_custom_chart(self, data, chart_type):
    # Your custom chart generation logic
    return chart_specification
```

## 🤝 **Contributing**

### **Code Style**
- Follow PEP 8 guidelines
- Use type hints throughout
- Comprehensive docstrings for all functions
- Clear error messages and logging

### **Testing**
- Test each component individually
- Integration tests for the complete workflow
- Performance benchmarking
- Error scenario testing

## 📚 **References**

### **Key Technologies**
- **Google Gemini API** - Natural language understanding and SQL generation
- **FAISS** - Vector similarity search for data discovery
- **PostgreSQL** - Database backend
- **Chart.js** - Frontend chart rendering

### **Related Documentation**
- [Gemini API Documentation](https://ai.google.dev/docs)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Chart.js Documentation](https://www.chartjs.org/docs/)

## 🎉 **Success Stories**

This system successfully handles complex queries like:

- ✅ "Make a bar chart of customer registrations in Australia by year"
- ✅ "Show me total sales by product category with trend analysis"
- ✅ "Find the top 10 customers by purchase frequency in the last quarter"
- ✅ "Create a line chart of monthly revenue trends by region"

## 🔮 **Future Enhancements**

### **Planned Features**
- **Multi-language support** for international queries
- **Advanced chart types** (heatmaps, 3D visualizations)
- **Query optimization** suggestions
- **Performance analytics** dashboard
- **Batch processing** for multiple queries

### **Integration Opportunities**
- **Real-time data** streaming
- **Mobile app** support
- **Voice interface** integration
- **Collaborative query** building

---

**Built with ❤️ using your existing components and enhanced with intelligent AI orchestration.**
