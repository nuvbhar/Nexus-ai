# Code Conventions

**Analysis Date:** 2026-09-09

## Code Style
- **Python**: Uses modern Python 3 features (`from __future__ import annotations`), standard logging (`logging.getLogger`). Follows PEP-8 generally but loosely. Configuration is loaded centrally via `core/config.py`. FastAPI for REST and WebSocket servers.
- **C++**: Follows Qt framework idioms (`QObject`, signals and slots). Uses modern C++ features (lambdas, namespaces). Contains platform-specific UI integration logic (e.g., `#ifdef Q_OS_WIN` for DWM APIs).

## Naming Conventions
- **Python**: `snake_case` for variables, functions, and module names. `PascalCase` for classes. Constant values (e.g., inside `Config`) use `UPPER_SNAKE_CASE`.
- **C++**: `PascalCase` for class names (`DynamicIslandWindow`, `WebSocketClient`). `camelCase` for methods, variables, and Qt properties.

## Architecture & Patterns
- **Backend (Python)**:
  - Centralized configuration via `.env` parsed into a `Config` singleton class.
  - Layered architecture with modules for `ai`, `api`, `core`, `memory`, and `tasks`.
  - State and storage managed locally in configured directories (`Documents/Nexus`).
- **Frontend (C++)**:
  - Event-driven using Qt signals and slots for asynchronous communication (e.g., bridging `WebSocketClient` with `DynamicIslandWindow`).
  - Server-driven state logic streamed over WebSockets.

## Error Handling
- **Python**: Standard `try/except` blocks. In web contexts, exceptions are logged (`logger.exception`) and graceful JSON responses or WebSocket error messages are sent back to the client.
- **C++**: Errors are typically communicated via Qt signals (e.g., `connectionError`) and handled with `qDebug` logging or visual state updates.

*Codebase conventions analysis: 2026-09-09*
<!-- refreshed: 2026-09-09 -->
