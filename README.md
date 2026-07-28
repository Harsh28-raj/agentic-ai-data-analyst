# DataMind AI — Enterprise Data Analyst (Groq Cloud Edition)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/Groq_Cloud-f43f5e?style=for-the-badge&logo=openai)](https://console.groq.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render)](https://render.com/)

**DataMind AI** is a production-ready, autonomous AI Data Analyst. It allows users to upload single or multi-CSV datasets and interact with their data using natural language. 

Powered by the **Groq Cloud API (`llama-3.3-70b-versatile`)** and a **LangGraph ReAct agent architecture**, DataMind AI answers analytical questions, generates interactive Plotly visualizations, transparently reveals its DuckDB SQL/Pandas code, performs statistical anomaly detection (IQR, Z-score, Isolation Forest), and instantly exports PDF/CSV executive reports.

---

## 🏗 Architecture & Folder Structure

```text
📦 datamind-ai
 ┣ 📂 agent/            # LangGraph ReAct Agent & LLM Tools
 ┣ 📂 api/              # FastAPI Backend Services
 ┃ ┣ 📂 endpoints/      # Modular REST Routes (upload, chat, dashboard)
 ┃ ┣ 📜 main.py         # FastAPI Entrypoint
 ┃ ┗ 📜 schemas.py      # Pydantic Request/Response Models
 ┣ 📂 core/             # Application Core Services
 ┃ ┣ 📜 config.py       # Pydantic Settings & Environment
 ┃ ┣ 📜 duckdb_manager.py # Zero-Copy In-Memory SQL Execution
 ┃ ┗ 📜 session.py      # Stateful Thread-Safe Session Store & Garbage Collector
 ┣ 📂 frontend/         # Streamlit Application
 ┃ ┣ 📂 pages/          # UI Views (Upload, Chat, Dashboard)
 ┃ ┣ 📜 app.py          # Streamlit Entrypoint
 ┃ ┗ 📜 style.css       # Premium Glassmorphism UI/UX
 ┣ 📜 render.yaml       # Render.com IaC Deployment Spec
 ┣ 📜 railway.json      # Railway PaaS Deployment Spec
 ┣ 📜 docker-compose.yml# Local Multi-Container Deployment
 ┗ 📜 requirements*.txt # Dependency Definitions
```

### 🧠 LangGraph Execution Flow
```mermaid
graph TD
    subgraph Frontend [Streamlit UI Multi-Page]
        UploadPage["1_Upload (Quality Audit)"]
        ChatPage["2_Chat (NL Streaming, PDF/CSV Exports)"]
        DashPage["3_Dashboard (Metrics & Anomalies)"]
    end

    subgraph API_Gateway [FastAPI Endpoints]
        UploadRouter["api/endpoints/upload.py"]
        ChatRouter["api/endpoints/chat.py"]
        DashRouter["api/endpoints/dashboard.py"]
    end

    subgraph AgentEngine [LangGraph ReAct Framework]
        GroqLLM["Groq API (llama-3.3-70b)"]
        Tools["Agent Tools (SQL, Charts, Anomalies)"]
        Cache["LRU Tool Caching"]
    end

    subgraph DataStore [Zero-Copy Storage]
        DuckDB["DuckDB Thread-Safe Memory Pool"]
        GarbageCollector["TTL Session GC"]
    end

    UploadPage --> UploadRouter
    ChatPage --> ChatRouter
    DashPage --> DashRouter

    UploadRouter --> DataStore
    DashRouter --> DuckDB
    ChatRouter <--> AgentEngine

    AgentEngine <--> GroqLLM
    AgentEngine <--> Tools
    Tools <--> DuckDB
    DataStore <--> GarbageCollector
```

---

## 🚀 Deployment Guide

DataMind AI is built for immediate deployment across multiple PaaS providers and local Docker environments.

### 🐳 Docker Compose (Local)
Spin up the decoupled frontend and backend instantly:
```bash
docker-compose up --build
```
- **Frontend**: `http://localhost:8501`
- **Backend API Docs**: `http://localhost:8000/docs`

### 🌐 Render
This repository includes a production-ready `render.yaml`.
1. Connect this GitHub repository to Render.
2. Select **New Blueprint Instance**.
3. Render will automatically provision both the FastAPI backend and Streamlit frontend.

### 🚂 Railway
This repository includes a `railway.json`.
1. Connect your repository to Railway.
2. Railway will parse the configuration and build the environment via Nixpacks.

### ☁️ Streamlit Cloud
1. Deploy `frontend/app.py` directly to Streamlit Community Cloud.
2. Set the `BACKEND_URL` environment variable in your Streamlit Cloud settings to point to your live FastAPI backend.
3. The `.streamlit/config.toml` will ensure the dark-mode theme remains synchronized.

---

## ⚙️ Local Development Setup

1. **Clone & Environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Backend**:
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Frontend**:
```bash
pip install -r requirements-frontend.txt
streamlit run frontend/app.py
```

---

## 📄 Licensing & Security
- **Data Privacy**: CSV data resides entirely within the ephemeral DuckDB memory pool and is purged aggressively by the Session Garbage Collector. No data is stored persistently to disk.
- **API Integrity**: Ensure `GROQ_API_KEY` is secured in your cloud platform's secret manager.
