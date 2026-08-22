# AI-Powered Project Design & Validation System 🚀

A full-stack, multi-agent AI application designed to help developers architect and validate personal software projects.

This system acts as an AI software architect: it can generate comprehensive technical design documents from a simple prompt, and it can evaluate user-submitted architectures against best practices using Advanced Retrieval-Augmented Generation (RAG).

## 🌐 Live Demo
* **Frontend Web App:** [agentic-chatbot-olive.vercel.app](https://agentic-chatbot-olive.vercel.app/)
* **Backend API Docs (Swagger UI):** [Azure Container Apps API Docs](https://backend-api.grayhill-ce67bd2c.southeastasia.azurecontainerapps.io/docs)

## ✨ Features
* **Agentic Workflow:** Utilizes a stateful LangGraph swarm to route asynchronous tasks and decision workflows.
* **Advanced RAG (Corrective & Self-RAG):** Dynamically validates, corrects, and reflects on retrieved contexts to eliminate AI hallucinations.
* **Vector Semantic Search:** Uses PostgreSQL with `pgvector` for high-throughput embedding storage and fast similarity retrieval.
* **Full-Stack Integration:** A responsive React frontend connected to a fast, asynchronous FastAPI backend.
* **Cloud Native:** Containerized backend deployed on Azure Container Apps with frontend hosting on Vercel.

## 🛠️ Tech Stack
* **Frontend:** React, Vite, TailwindCSS, Axios
* **Backend:** Python, FastAPI, Uvicorn
* **AI & Orchestration:** LangGraph, LangChain, Google Gemini API, LangSmith (for tracing)
* **Database:** PostgreSQL (hosted on Neon) with `pgvector`
* **Deployment:** Docker, Azure Container Apps, Vercel

---

