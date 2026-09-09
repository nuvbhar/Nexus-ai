# Codebase Structure

**Analysis Date:** 2026-09-09

## Directory Layout

The repository is divided into two primary domains: the C++ Qt Frontend and the Python Backend.

```
Nexus/
├── CMakeLists.txt                 # Build configuration for the C++ Qt6 application
├── main.cpp                       # Application entry point for the C++ UI
├── DynamicIslandWindow.cpp/.h     # Core UI widget for the Dynamic Island presentation
├── backend/                       # Python backend and services
│   ├── main.py                    # Entry point for the Uvicorn FastAPI server
│   ├── WebsocketClient.cpp/.h     # C++ WebSocket client classes (included in frontend build)
│   ├── api/                       # API layer and endpoints
│   │   ├── server.py              # FastAPI application and WebSocket route definitions
│   │   └── email/                 # IMAP integration, parsing, and context management
│   ├── ai/                        # AI operations
│   │   ├── ai_manager.py          # Wrapper for llama-cpp-python
│   │   └── tool_router.py         # Intent parsing and prompt injection middleware
│   ├── core/                      # Core backend utilities
│   │   └── config.py              # Environment and path configurations (loads .env)
│   ├── memory/                    # Persistent memory management
│   │   ├── parser.py              # NLP parsing for memory intents (Regex-based)
│   │   ├── router.py              # Routes memory operations to storage CRUD operations
│   │   └── storage.py/service.py  # JSON file manipulation for memory domains
│   ├── tasks/                     # Agent task and checklist management
│   │   └── service.py             # Logic for managing JSON agent task checklists
│   └── models/                    # Directory for local GGUF model binaries
```

## Key Locations
- **UI Logic:** `DynamicIslandWindow.cpp` is the focal point for all frontend UI rendering, containing specialized logic for Mac-like dynamic island animations and coalesced text streaming.
- **Routing & Intent Engine:** `backend/ai/tool_router.py` is the most critical file for extending AI capabilities. It determines when to trigger tools and inject context.
- **Memory Intent Parsing:** `backend/memory/parser.py` contains the regex and keyword dictionaries used to interpret user memory requests (deadlines, projects, tasks).
- **Configuration & Paths:** `backend/core/config.py` dictates where data is saved. Standard storage locations resolve to `~/Documents/Nexus` (for persistent data) and temporary directories for ephemeral chat history.

## Naming Conventions
- **C++:** Uses `PascalCase` for classes and filenames (e.g., `DynamicIslandWindow.cpp`), `camelCase` for methods/variables, and `m_` prefix for private member variables (Qt standard).
- **Python:** Follows PEP-8 with `snake_case` for filenames, variables, and functions, and `PascalCase` for classes.
- **Storage:** JSON data files use `snake_case` (e.g., `agent_tasks.json`, `history.json`).

<!-- refreshed: 2026-09-09 -->
*Nexus structure analysis: 2026-09-09*
