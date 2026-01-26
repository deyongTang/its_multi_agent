# ITS Multi-Agent System (its_app)

## Project Overview

This project is an industrial-grade **Intelligent Transport System (ITS) Multi-Agent** backend application. It is designed to provide "Business Data Closed Loop" and "Controllable Business Processes" using a sophisticated multi-agent architecture.

The core functionality involves an **Orchestrator Agent** that coordinates various specialized agents and tools to handle complex user requests (e.g., combining real-time information with technical support or POI navigation). It utilizes the **Model Context Protocol (MCP)** to standardize connections to external services like Baidu Maps and search engines.

## Tech Stack

*   **Language:** Python 3.x
*   **Web Framework:** FastAPI (with Uvicorn)
*   **AI & LLM:** OpenAI-compatible clients (SiliconFlow, Alibaba Bailian).
    *   **Main Model:** Qwen/Qwen3-32B (Reasoning)
    *   **Sub Model:** qwen3-max (Execution/Tool Use)
*   **Database:** MySQL (pymysql, DBUtils)
*   **Configuration:** Pydantic Settings
*   **Protocols:** Model Context Protocol (MCP)
*   **Networking:** STUN (pystun3)

## Architecture

The project follows a Domain-Driven Design (DDD) inspired layered architecture:

*   **`api/`**: Web layer. Contains FastAPI app entry point (`main.py`) and routers (`routers.py`).
*   **`multi_agent/`**: Core agent logic. Contains the `OrchestratorAgent`, `AgentFactory`, and specific agent implementations.
*   **`services/`**: Business logic layer. Bridges the API and the Agents (e.g., `AgentService`, `SessionService`).
*   **`infrastructure/`**: Low-level implementations.
    *   `ai/`: LLM client wrappers and prompt loading.
    *   `database/`: Database connection pooling.
    *   `tools/`:
        *   `mcp/`: **Model Context Protocol** manager and server implementations (Baidu, Search).
        *   `local/`: Local tools (Knowledge Base, Service Station).
*   **`config/`**: Configuration management via `settings.py`.
*   **`schemas/`**: Pydantic models for Request/Response validation.

## Setup & Configuration

1.  **Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    The application relies on a `.env` file in the project root. Key configurations include:
    *   **AI Services:** `SF_API_KEY`, `SF_BASE_URL` (SiliconFlow) OR `AL_BAILIAN_API_KEY` (Alibaba).
    *   **Database:** `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.
    *   **External Tools:** `BAIDUMAP_AK`, `DASHSCOPE_API_KEY`.

## Running the Application

### 1. Start the API Server
The main entry point runs a Uvicorn server.

```bash
python api/main.py
```
*   **Port:** 8000
*   **Host:** 127.0.0.1
*   **Endpoints:**
    *   `POST /api/query`: Main chat interface (SSE stream).
    *   `POST /api/user_sessions`: Retrieve chat history.

### 2. Run Agent Tests (CLI)
You can run the Orchestrator Agent directly to test logic without the web server.

```bash
python multi_agent/orchestrator_agent.py
```
*   This executes defined `test_cases` in the `main()` function.
*   It demonstrates the "Thought" process and "Tool Calls" in the console.

## Key Features

### Orchestrator Agent
*   Located in `multi_agent/orchestrator_agent.py`.
*   Uses a "Reasoning Model" (e.g., DeepSeek R1 via Qwen) to break down tasks.
*   Delegates sub-tasks to tools or other agents.
*   Supports streaming responses.

### MCP (Model Context Protocol)
*   Located in `infrastructure/tools/mcp/`.
*   Standardizes how the AI connects to `baidu_mcp_client` and `search_mcp_client`.
*   Managed via `mcp_manager.py` which handles connection lifecycle (connect on startup, cleanup on shutdown).

## Development Notes
*   **Logging:** Centralized logger in `infrastructure/logging/logger.py`.
*   **Session Management:** User sessions are stored (likely in MySQL) and retrieved via `SessionRepository`.
*   **Prompts:** Prompts are externalized in `prompts/*.md` and loaded via `prompt_loader.py`.
