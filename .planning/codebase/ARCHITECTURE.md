# Codebase Architecture

**Analysis Date:** 2026-09-09

## Overview
Nexus AI is a local-first AI assistant featuring a "Dynamic Island" style desktop widget. The architecture follows a strict Client-Server pattern communicating over WebSockets, with a clear separation of concerns between the presentation layer (C++/Qt) and the AI/Backend logic (Python/FastAPI).

## High-Level Pattern & Layers

### 1. Presentation Layer (Frontend)
- **Technology:** C++20, Qt6 (Widgets, Network, WebSockets)
- **Pattern:** Thick UI client with dumb logic. It handles purely visual aspects such as geometry animations, Windows dwmapi (for acrylic/blur effects), state transitions (Idle, Compact, Expanded), and visual activity indicators.
- **Responsibility:** Incremental streaming of AI responses to a `QTextBrowser` via `QTextCursor` for smooth 30FPS rendering, completely decoupled from AI reasoning.

### 2. API & Communication Layer
- **Technology:** Python, FastAPI, WebSockets (`uvicorn`)
- **Pattern:** Asynchronous WebSocket server (`/ws`).
- **Responsibility:** Accepts user prompts, manages WebSocket lifecycles, and streams LLM tokens and status indicators back to the client.

### 3. Tool Routing & Intent Layer
- **Pattern:** Prompt Interception & Injection (Regex/Keyword based).
- **Responsibility:** Instead of standard ReAct or tool-calling loops, the `ToolRouter` acts as a middleware. It analyzes the user prompt before sending it to the LLM to detect intents (e.g., memory read/write, email summaries).
- **Data Flow:** If an intent is detected, it interacts with backend services (Memory, Email), retrieves context, and injects it into a `SYSTEM` prompt to strictly bound the LLM's response generation to factual retrieved data.

### 4. AI & Generation Layer
- **Technology:** `llama_cpp` (Python bindings) running local GGUF models.
- **Responsibility:** The `AIManager` loads the model and handles prompt execution and token streaming. It takes the enriched prompts from the `ToolRouter` and conversation history to generate responses.

### 5. Services & Storage Layer
- **Services:** `TaskService` (Agent tasks/checklists), `EmailService` (IMAP integration), and `MemoryRouter` (CRUD for tasks, deadlines, projects).
- **Storage:** File-based JSON persistence. Persistent data (tasks, memory) is stored in the user's `Documents/Nexus` directory, while ephemeral data (conversation history) is stored in system temporary directories.

## Data Flow
1. **Input:** User types a prompt in the Qt Dynamic Island and hits enter.
2. **Transport:** `WebsocketClient.cpp` serializes the message and sends it to `ws://127.0.0.1:8000/ws`.
3. **Intercept:** FastAPI `server.py` receives the prompt and passes it to `ToolRouter`.
4. **Enrichment:** `ToolRouter` parses the intent (e.g., "What are my deadlines?"). It calls `MemoryRouter`, which fetches JSON data. `ToolRouter` constructs a new prompt with the factual data injected as a `SYSTEM` message.
5. **Generation:** The enriched prompt and conversation history are passed to `AIManager.generate_stream()`.
6. **Streaming Response:** Tokens are yielded back to the WebSocket endpoint, which streams them to the C++ client (`handleToken`).
7. **Rendering:** The Qt UI coalesces tokens and injects them via `QTextCursor`, animating the height of the island dynamically.

## Entry Points
- **Client:** `main.cpp` -> Initializes the Qt Application and spawns the `DynamicIslandWindow`.
- **Server:** `backend/main.py` -> Runs the Uvicorn ASGI server hosting the FastAPI `app` from `backend/api/server.py`.

<!-- refreshed: 2026-09-09 -->
*Nexus architecture analysis: 2026-09-09*
