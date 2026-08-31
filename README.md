# AI Kubernetes Agent

> **An AI-powered DevOps troubleshooting agent for investigating Kubernetes clusters, identifying root causes, and generating actionable remediation steps.**

AI Kubernetes Agent combines **Kubernetes observability, automated cluster investigation, DevOps troubleshooting, and AI-assisted root-cause analysis** into a single platform.

Instead of manually running multiple `kubectl` commands and inspecting logs, events, deployments, and networking, the agent performs the investigation automatically and uses an LLM to explain the findings and suggest fixes.

---

## Screenshots

### Dashboard

![image alt](https://github.com/Atharv28ye/ai-kubernetes-management/blob/bcd801eafbaeb93dcf33cc2e479dbb46a8643059/1.png)

### Kubernetes Investigation

![image alt](https://github.com/Atharv28ye/ai-kubernetes-management/blob/bcd801eafbaeb93dcf33cc2e479dbb46a8643059/2.png)

### Root Cause Analysis

![image alt](https://github.com/Atharv28ye/ai-kubernetes-management/blob/bcd801eafbaeb93dcf33cc2e479dbb46a8643059/3.png)

### Dashboard History
![image alt](https://github.com/Atharv28ye/ai-kubernetes-management/blob/bcd801eafbaeb93dcf33cc2e479dbb46a8643059/4.png)
---

# Architecture

```text
                         ┌──────────────────────┐
                         │      Developer       │
                         │        / SRE         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Next.js Frontend   │
                         │ TypeScript + Tailwind│
                         └──────────┬───────────┘
                                    │ REST API
                                    ▼
                         ┌──────────────────────┐
                         │   FastAPI Backend    │
                         │    API Orchestrator  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Kubernetes Investigation     │
                    │            Layer              │
                    └──────────────┬────────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
             ▼                     ▼                     ▼
      ┌────────────┐       ┌────────────┐       ┌────────────┐
      │    Pods    │       │ Deployments│       │  Services  │
      └────────────┘       └────────────┘       └────────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │ Events + Logs +      │
                         │ Network Information  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  AI Kubernetes Agent │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ LLM Reasoning Layer  │
                         │      OpenRouter      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Root Cause Analysis  │
                         │ Suggested Fix        │
                         │ kubectl Commands     │
                         │ Prevention Steps     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Frontend Diagnosis   │
                         └──────────────────────┘



## Why This Project?

Troubleshooting Kubernetes incidents often requires checking multiple layers:

```text
Kubernetes Cluster
        │
        ▼
Cluster Discovery
        │
        ▼
Select Kubernetes Context
        │
        ▼
Start Investigation
        │
        ▼
Inspect Pods
        │
        ▼
Collect Container Logs
        │
        ▼
Analyze Kubernetes Events
        │
        ▼
Inspect Deployments
        │
        ▼
Inspect Services
        │
        ▼
Inspect Network Configuration
        │
        ▼
Aggregate Cluster Evidence
        │
        ▼
AI Reasoning
        │
        ▼
Root Cause Diagnosis
        │
        ▼
Suggested Remediation
        │
        ▼
kubectl Commands
        │
        ▼
Investigation History

Tech Stack

1)DevOps and Infrastructure
Kubernetes
kubectl
Minikube
Kind
Docker
Docker Compose

2)Backend
Python 3.12+
FastAPI
Uvicorn
Pydantic
HTTPX
Loguru

3)Frontend
Next.js
React
TypeScript
Tailwind CSS

4)AI
OpenRouter
LLM based reasoning
AI powered root cause analysis
Data and Services
JSON based investigation history
InsForge integration


Project Structure
ai-kubernetes-management/
│
├── backend/
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── clusters.py
│   │   └── investigation.py
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── ai_agent.py
│   │   ├── llm_client.py
│   │   └── prompt_builder.py
│   │
│   ├── kubectl/
│   │   ├── __init__.py
│   │   ├── kubeconfig_reader.py
│   │   └── kubectl_executor.py
│   │
│   ├── kubernetes/
│   │   ├── __init__.py
│   │   ├── deployment_inspector.py
│   │   ├── events_analyzer.py
│   │   ├── logs_collector.py
│   │   ├── network_inspector.py
│   │   └── pod_inspector.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── history_service.py
│   │   ├── investigation_service.py
│   │   └── realtime_service.py
│   │
│   ├── data/
│   │   └── investigation_history.json
│   │
│   ├── models/
│   ├── core/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   │
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── ClusterSelector.tsx
│   │   ├── InvestigateButton.tsx
│   │   ├── InvestigationHistory.tsx
│   │   ├── InvestigationProgress.tsx
│   │   ├── RootCauseCard.tsx
│   │   └── ui/
│   │       └── Button.tsx
│   │
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── package.json
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── .env.example
│
├── migrations/
│
├── test-scenarios/
│   ├── crashloopbackoff-deployment.yaml
│   ├── imagepullbackoff-deployment.yaml
│   ├── oomkilled-deployment.yaml
│   ├── service-selector-mismatch.yaml
│   ├── deploy-test-scenarios.sh
│   └── cleanup-test-scenarios.sh
│
├── docker-compose.yml
├── README.md
├── TESTING.md
├── FINAL_STATUS.md
└── .gitignore






