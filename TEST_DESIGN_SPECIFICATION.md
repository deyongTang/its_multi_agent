# ITS System Acceptance Test Design Specification (v1.0)

## 1. Document Overview
*   **Project Name**: ITS (Intelligent Transport System) Multi-Agent & Knowledge Base
*   **Version**: v1.0
*   **Target Audience**: Architects, Developers, QA Engineers, DevOps
*   **Purpose**: To define the system's acceptance criteria, testing strategy, and specific test case designs, ensuring deliverables meet industrial-grade quality standards.

## 2. Scope & Strategy

### 2.1 Test Layering Model (The Testing Pyramid)
This system adopts a standard pyramid testing strategy with the following resource allocation:

| Layer | Type | Coverage Goal | Core Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | **Unit Testing** | Logic Coverage > 80% | White-box testing, Mocking external dependencies | Dev |
| **L2** | **Integration Testing** | Interface Coverage 100% | Grey-box testing, Real Docker environments (Middleware) | Dev/QA |
| **L3** | **E2E/Scenario Testing** | Core Business Paths 100% | Black-box testing, Simulating real user behavior | QA/Product |
| **L4** | **Non-functional Testing** | Performance/Security/HA | Load testing, Chaos engineering, Security scanning | Arch/Ops |

### 2.2 Critical Testing Areas
1.  **Data Consistency**: The Knowledge Base ETL pipeline (Crawl -> Clean -> Store -> Index) must guarantee zero data loss, no duplicates, and traceable versioning.
2.  **Agent Reasoning**: LangGraph state transitions must be deterministic and loop-free; tool invocation parameters must be accurate.
3.  **Retrieval Accuracy**: Hybrid Search (Elasticsearch + Vector) + RRF Re-ranking must empirically outperform single-mode retrieval.
4.  **Concurrency Stability**: System must remain stable under high concurrency without race conditions or deadlocks (especially involving MySQL transactions and ES writes).

## 3. Environment Design

### 3.1 Topology
To ensure reproducibility, all integration tests must run within an isolated **Docker Compose** orchestrated environment.

*   **SUT (System Under Test)**:
    *   `backend/app` (FastAPI + LangGraph Orchestrator)
    *   `backend/knowledge` (FastAPI + Ingestion Worker)
*   **Infrastructure (Mock/Real)**:
    *   **MySQL** (Real, initialized via `init_db.py`)
    *   **Elasticsearch** (Real, single node, 8.x)
    *   **MinIO** (Real, local bucket)
    *   **Redis** (Real, for caching/distributed locks)
    *   **LLM API** (Mock via `vcrpy` for stability in L1/L2; Real for L3)
    *   **External Tools** (Mock via `respx` for deterministic results in L1/L2)

### 3.2 Data Management
*   **Static Data**: A pre-provisioned "Golden Dataset" containing ~50 Markdown files covering edge cases (e.g., complex traffic rules, tables, noisy HTML).
*   **Dynamic Data**: Temporary data generated during runtime, automatically cleaned up via `teardown` fixtures.

## 4. Test Case Design

### 4.1 Module A: Knowledge Base (`backend/knowledge`)

| ID | Component | Scenario | Pre-condition | Steps | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KB-01** | Sync | **Idempotency & Deduplication** | MinIO/DB Empty | 1. Upload File A (Hash=X)<br>2. Upload File A again (Hash=X)<br>3. Upload Modified File A (Hash=Y) | 1. Success, DB Status=NEW<br>2. Returns `duplicate`, No DB change<br>3. Success, Version increments | **P0** |
| **KB-02** | RAG | **RRF Algorithm Accuracy** | Index has specific docs | 1. Construct Query where Keyword hits Doc A (Rank 1) & Vector hits Doc B (Rank 1)<br>2. Adjust weights | Final ranking order of Doc A & B matches RRF formula calculation | **P1** |
| **KB-03** | Worker | **Task Retry Mechanism** | Stop ES Service | 1. Push Task to DB (Status=NEW)<br>2. Start Worker<br>3. Worker fails to process<br>4. Start ES<br>5. Trigger Retry | 1. Task status becomes ERROR<br>2. After retry, status becomes COMPLETED<br>3. Error logs are clear | **P1** |
| **KB-04** | Crawler | **Dirty Data Cleaning** | None | 1. Simulate HTML response with `<script>` tags and encoding errors | Markdown output is clean, script tags removed, filename is valid | **P2** |

### 4.2 Module B: Multi-Agent (`backend/app`)

| ID | Component | Scenario | Pre-condition | Steps | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AG-01** | LangGraph | **Intent Routing Accuracy** | None | 1. Input "Check violation for京A88888" (Info)<br>2. Input "Navigate to Airport" (Map)<br>3. Input "Hello" (Chat) | 1. Route to `query_knowledge`<br>2. Route to `query_local_tools`<br>3. Route to `general_chat` | **P0** |
| **AG-02** | Workflow | **Slot Filling Loop** | None | 1. User intent requires param (e.g., destination)<br>2. User provides partial info<br>3. Agent asks for missing info<br>4. User provides missing info | Agent enters `slot_filling` loop until all params are present, then transitions to execution | **P1** |
| **AG-03** | MCP | **Tool Protocol Compatibility** | Start MCP Server | 1. Agent triggers `search_map` tool | MCP Client serializes params correctly, Server responds, Result parsed back to Agent context | **P1** |
| **AG-04** | Session | **Persistence & Recovery** | MySQL Normal | 1. User A starts Session 1<br>2. Restart Service<br>3. User A resumes Session 1 | Context from Session 1 is correctly loaded and used in response | **P1** |

## 5. Entry & Exit Criteria

### 5.1 Entry Criteria
*   Test Design Specification reviewed and approved.
*   Code compiles successfully with no P0 static analysis errors (Lint/Type Check).
*   Test Environment (Docker) can be provisioned automatically.

### 5.2 Exit Criteria
*   **Functionality**: 100% Pass rate for all P0/P1 cases in L1/L2/L3.
*   **Coverage**: Core business logic Line Coverage > 80%.
*   **Defects**: Zero open Critical or Major bugs.
*   **Documentation**: Comprehensive Test Report generated.

## 6. Risk Analysis & Mitigation

| Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **OpenAI/LLM API Instability** | High | Blocks Testing | 1. Use `vcrpy` to record/replay API interactions in L1/L2.<br>2. Implement retry logic with exponential backoff in L3. |
| **Dirty Reads/Writes in ES/MySQL** | Medium | Flaky Tests | 1. Strict `setup` and `teardown` fixtures to clean data.<br>2. Use dedicated test databases/indices. |
| **LangGraph Non-determinism** | Medium | Hard to Debug | 1. Set LLM `temperature=0` in test config.<br>2. Enable verbose state snapshot logging for traceability. |
