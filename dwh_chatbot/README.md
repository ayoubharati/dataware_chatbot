# DataWare Chatbot

A React-based frontend for an AI-powered data warehouse chatbot that connects to a Flask backend.

## Features

- Clean, modern UI built with React and Tailwind CSS
- Real-time chat interface for data warehouse queries
- Integration with Flask backend for AI-powered responses
- Responsive design with sidebar navigation

## Prerequisites

- Node.js (v16 or higher)
- Python 3.8+ with Flask backend running
- The Flask backend should be running on `http://localhost:5000`

## Installation

1. Install frontend dependencies:
```bash
npm install
```

2. Make sure your Flask backend is running in the `chat_backend/` directory:
```bash
cd ../chat_backend
python app.py
```

## Running the Application

1. Start the development server:
```bash
npm run dev
```

2. Open your browser and navigate to `http://localhost:5173`

3. Use any email/password combination to log in (authentication is simplified for demo purposes)

## Usage

1. **Login**: Enter any email and password to access the chatbot
2. **New Chat**: Click "New Chat" to start a fresh conversation
3. **Ask Questions**: Type natural language queries about your data warehouse
4. **Get AI Responses**: The system will process your query through the Flask backend and return AI-generated insights

## API Integration

The frontend communicates with the Flask backend using the `/query` endpoint:

```javascript
const response = await fetch('http://localhost:5000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: "your question here",
    per_term_k: 10,
    whole_query_k: 10,
    call_gemini: true
  })
});
```

## Project Structure

```
dwh_chatbot/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx    # Main chat interface
│   │   └── Login.jsx           # Login component
│   ├── App.jsx                 # Main application component
│   └── main.jsx                # Application entry point
├── package.json
└── README.md
```

## Technologies Used

- **Frontend**: React 19, Tailwind CSS, Vite
- **Icons**: Lucide React
- **Backend Integration**: Fetch API for HTTP requests
- **Styling**: Tailwind CSS with custom gradients and animations

## Development

- The application uses React hooks for state management
- Tailwind CSS for responsive design
- CORS is enabled on the backend for frontend communication
- Error handling for network requests and API responses
