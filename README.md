# DataWare Chatbot

## 📖 Overview

**DataWare Chatbot** is an AI-powered web application for querying data warehouses using natural language, featuring a React frontend and a Flask backend. It orchestrates modules to transform questions into validated SQL queries and chart visualizations, powered by Google Gemini and FAISS.

---

## 🛠️ Prerequisites

- Node.js (v16+ recommended)
- Python 3.8+ (Flask; install dependencies from `requirements.txt`)
- PostgreSQL database running `dataware_test`
- **Google Gemini API key dropped in backend configuration**

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd chat_backend
# Install Python dependencies
pip install -r requirements.txt

# Set up your Google Gemini API key and DB credentials in config.py
# (Be sure config.py contains your secrets; do NOT commit them!)

# Start Flask backend
python app.py
```
- Ensure the backend runs on `http://localhost:5000` or `5001`.
- Confirm DB and API keys are correct in config.

---

### 2. Frontend Setup

```bash
cd dwh_chatbot
npm install
npm run dev
```
- Opens frontend at `http://localhost:5173`.

---

## 💻 Launch Sequence

1. **Run backend** (Flask, with API key set).
2. **Run frontend** (`npm run dev`).
3. Open browser at [http://localhost:5173](http://localhost:5173).

---

## 🔌 API Notes

- The backend expects requests to the `/query` endpoint.
- Set your Google Gemini API key in the backend config.

---

## 🖼️ Screenshots & Diagrams

### Architecture / Flow Diagram

<div style="display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; margin: 30px 0;">

  <div style="text-align: center; flex: 1 1 380px; max-width: 480px;">
    <img src="https://github.com/user-attachments/assets/e3eb8901-aebc-4c84-be81-695c867817da" alt="Architecture / Flow Diagram" width="480" style="border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);"/>
  </div>

  <!-- Example 1 -->
  <div style="text-align: center; flex: 1 1 380px; max-width: 480px;">
    <img src="https://github.com/user-attachments/assets/ec95b5c6-efdc-4428-8ca1-8060086ac31a" alt="Example result 1" width="480" style="border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);"/>
    <p><em>###########################</em></p>
  </div>

  <!-- Example 2 -->
  <div style="text-align: center; flex: 1 1 380px; max-width: 480px;">
    <img src="https://github.com/user-attachments/assets/dc6cc658-e97c-434d-b917-e632f8d1afda" alt="Example result 2" width="480" style="border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);"/>
    <p><em>###########################</em></p>
  </div>

  <!-- Example 3 -->
  <div style="text-align: center; flex: 1 1 380px; max-width: 480px;">
    <img src="https://github.com/user-attachments/assets/b418c908-6210-4b74-9532-7ef66ac47562" alt="Example result 3" width="480" style="border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);"/>
    <p><em>###########################</em></p>
  </div>

  <!-- Example 4 -->
  <div style="text-align: center; flex: 1 1 380px; max-width: 480px;">
    <img src="https://github.com/user-attachments/assets/9e32b563-b99f-4a44-a1ea-3b949476a490" alt="Example result 4" width="480" style="border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);"/>
    <p><em>###########################</em></p>
  </div>

</div>

## 📦 Technologies

- React 19, Vite, Tailwind CSS
- Flask, Pandas, SQLAlchemy
- Google Gemini AI
- FAISS, Plotly, Chart.js

---

## 📝 Contributing

- See `chat_backend/query_generation/README.md` for contributing guidelines.

---

## 📚 References

- [FAISS](https://github.com/facebookresearch/faiss)
- [React Documentation](https://react.dev/)
- [Google Gemini API](https://ai.google.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [Plotly](https://plotly.com/python/)

---
