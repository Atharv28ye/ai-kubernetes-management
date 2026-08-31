# AI Kubernetes Agent

An AI-powered Kubernetes troubleshooting agent that helps diagnose and resolve cluster issues using intelligent reasoning.

## Architecture

```
Frontend (Next.js)
    ↓
FastAPI Backend (Orchestrator)
    ↓
Kubernetes Investigation Layer
    ↓
AI Kubernetes Agent
    ↓
LLM Reasoning (OpenRouter via InsForge)
    ↓
Root Cause + Suggested Fix
    ↓
Frontend Diagnosis
```

## Tech Stack

### Backend
- FastAPI
- Python 3.12+
- Uvicorn
- Pydantic
- Loguru
- HTTPX

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- Axios
- React Query

### Infrastructure
- Docker
- Docker Compose

## Project Structure

```
ai-kubernetes-agent/
├── backend/
│   ├── api/           # API endpoints
│   ├── core/          # Core configuration and utilities
│   ├── kubernetes/    # Kubernetes investigation module
│   ├── ai/            # AI reasoning module
│   ├── services/      # Business logic services
│   ├── models/        # Data models and schemas
│   ├── main.py        # FastAPI application entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/           # Next.js app directory
│   ├── components/    # React components
│   ├── services/      # API services
│   ├── hooks/         # Custom React hooks
│   ├── types/         # TypeScript types
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docs/              # Documentation
├── prompts/           # AI prompts
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Environment Variables

#### Backend (`backend/.env`)
```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
KUBECONFIG_PATH=
```

#### Frontend (`frontend/.env`)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Running the Application

1. Clone the repository
2. Copy environment examples:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
3. Start the services:
   ```bash
   docker compose up --build
   ```

### Access the Application

- Frontend: http://localhost:3000
- Backend Health: http://localhost:8000/health
- Backend API Docs: http://localhost:8000/docs

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## Current Status

This is the initial project setup. The following features are implemented:
- ✅ FastAPI backend with health endpoint
- ✅ Next.js frontend with minimal homepage
- ✅ Docker and Docker Compose configuration
- ✅ Project structure and placeholder modules

The following features are NOT yet implemented:
- ❌ Kubernetes investigation logic
- ❌ AI reasoning with OpenRouter
- ❌ InsForge integration
- ❌ Authentication
- ❌ Realtime updates

## License

MIT
