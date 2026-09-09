# Technology Stack

**Analysis Date:** 2026-09-09

## Languages & Runtime
- **Frontend:** C++ (Standard 20)
- **Backend:** Python 3
- **Runtime:** Native execution for Frontend (Windows), Python virtual environment for Backend

## Frameworks & Libraries
- **Frontend:** Qt6 (Widgets, Core, Network, WebSockets)
- **Backend:** 
  - FastAPI
  - Uvicorn (`uvicorn[standard]`)
  - Websockets
  - `llama-cpp-python` for local LLM inference

## Architecture & Communication
- **Architecture:** Local Client-Server model.
- **Protocol:** WebSocket for real-time bidirectional streaming (prompt requests, token streaming, state updates). The Python backend serves the AI stream and manages integrations.
- **Model:** Local GGUF format (e.g., `llama-3.2-3b-instruct.gguf`).

## Build & Dependencies
- **Build System (C++):** CMake (3.20+)
- **Dependency Management (Python):** `pip` using `requirements.txt`

## Configuration
- Environment variables via `.env` file (loaded using `python-dotenv`).

<!-- refreshed: 2026-09-09 -->
*Technology stack analysis: 2026-09-09*
