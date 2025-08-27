# 🚀 Frontend Integration with Query Generation Backend

This document explains how to integrate your React frontend with the new advanced query generation backend.

## 📁 **File Structure**

```
chat_backend/
├── app.py (existing - unchanged)
├── query_generation_app.py (NEW - advanced query service)
├── start_query_service.py (NEW - startup script)
├── query_generation/ (modular query system)
└── FRONTEND_INTEGRATION_README.md (this file)

dwh_chatbot/ (your React frontend)
├── src/components/
│   ├── Page.jsx (updated for new backend)
│   └── Chart.jsx (updated for new backend)
└── ... (other frontend files)
```

## 🔧 **Backend Setup**

### 1. Start the Query Generation Service

```bash
cd chat_backend
python start_query_service.py
```

This will start the service on **port 5001** with these endpoints:

- `GET /health` - Health check
- `POST /query/advanced` - Main query endpoint
- `GET /query/status` - Service status
- `POST /query/test` - Test individual components
- `POST /query/cleanup` - Reset the system

### 2. Service Status

The service will show:
```
🚀 Starting Query Generation Service...
   Service will run on: http://localhost:5001
✅ Query Generation Service started successfully!
```

## 🌐 **Frontend Integration**

### 1. Updated Components

Your frontend has been updated to work with the new backend:

- **`Page.jsx`** - Now calls `http://localhost:5001/query/advanced`
- **`Chart.jsx`** - Handles both Plotly and Chart.js data formats
- **Backend status indicator** - Shows connection status
- **7-step workflow display** - Shows execution steps

### 2. API Contract

The frontend now expects this response format:

```json
{
  "success": true,
  "resolvable": true,
  "result_type": "chart",
  "query": "SELECT * FROM customers...",
  "chart_data": { /* Chart.js format */ },
  "result": null,
  "message": "Here's your bar chart...",
  "workflow_steps": [
    {
      "name": "Step 1: Load Schema",
      "status": "success",
      "execution_time": 0.123
    }
    // ... more steps
  ],
  "execution_time": 1.234
}
```

### 3. Message Structure

Each assistant message now contains:

```javascript
{
  role: 'assistant',
  message: 'User-friendly message',
  timestamp: '2024-01-01T00:00:00.000Z',
  resolvable: true,
  result_type: 'chart', // 'chart', 'table', 'summary', 'text'
  query: 'SQL query string',
  chart_data: { /* Chart.js data */ },
  result: 'data for non-chart results',
  workflow_steps: [ /* execution steps */ ],
  execution_time: 1.234
}
```

## 🎯 **How It Works**

### 1. User Query Flow

1. User types a query in the frontend
2. Frontend sends POST to `http://localhost:5001/query/advanced`
3. Backend runs the 7-step workflow:
   - Load schema
   - Extract search terms
   - FAISS search
   - Check resolvability
   - Generate SQL
   - Test and validate
   - Generate final response
4. Frontend receives structured response
5. Frontend displays message, chart (if applicable), and query details

### 2. Chart Display

- **Chart.js data**: Shows placeholder with data info
- **Plotly data**: Renders interactive Plotly charts
- **Other data**: Shows data preview

### 3. Query Details

Users can expand to see:
- 7-step workflow execution
- Generated SQL query
- Result type and format
- Execution times
- Chart configuration (if applicable)

## 🚦 **Status Indicators**

The frontend shows backend connection status:

- 🟢 **Connected** - Ready to process queries
- 🔴 **Disconnected** - Backend service not running
- 🟡 **Checking...** - Checking connection status

## 🧪 **Testing**

### 1. Test Individual Components

```bash
curl -X POST http://localhost:5001/query/test \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "test_type": "extract_terms"}'
```

### 2. Test Full Query

```bash
curl -X POST http://localhost:5001/query/advanced \
  -H "Content-Type: application/json" \
  -d '{"query": "Make a bar chart of customer registrations in Australia by year"}'
```

### 3. Check Service Status

```bash
curl http://localhost:5001/health
```

## 🔄 **Migration from Old System**

### What Changed

- **Endpoint**: `http://localhost:5000/query` → `http://localhost:5001/query/advanced`
- **Response format**: New structured format with workflow steps
- **Chart data**: Chart.js compatible (with Plotly fallback)
- **Error handling**: Better error messages and status tracking

### What Stayed the Same

- **UI components**: Same React components, updated logic
- **User experience**: Same chat interface
- **Chart display**: Still uses Plotly for rendering

## 🚨 **Troubleshooting**

### 1. Backend Won't Start

- Check if port 5001 is available
- Ensure all dependencies are installed
- Check Python environment and packages

### 2. Frontend Can't Connect

- Verify backend is running on port 5001
- Check CORS settings
- Look for network errors in browser console

### 3. Charts Not Displaying

- Check if `chart_data` is in the response
- Verify data format (Chart.js vs Plotly)
- Check browser console for errors

### 4. Workflow Steps Missing

- Ensure backend is using the latest orchestrator
- Check if all 7 steps completed successfully
- Look for error messages in backend logs

## 🎉 **Next Steps**

1. **Start the backend**: `python start_query_service.py`
2. **Test the connection**: Visit `http://localhost:5001/health`
3. **Try a query**: Use the frontend to ask a question
4. **Monitor workflow**: Check the query details for execution steps

## 📞 **Support**

If you encounter issues:

1. Check backend logs for error messages
2. Verify all services are running
3. Test individual endpoints with curl
4. Check frontend console for network errors

The system is designed to be robust and provide clear feedback about what's happening at each step!
