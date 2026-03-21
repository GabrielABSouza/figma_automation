# Figma Automation Pipeline

## Project Overview

Pipeline de automação que converte intenção de produto (PRD/prompt/chat) em telas estruturadas renderizadas no Figma, usando multi-agent architecture com design system como constraint engine.

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, LangGraph
- **LLM:** Gemini (primary) via google-genai SDK, abstração via LLMProvider protocol
- **Figma:** Plugin TypeScript (renderer)
- **Storage:** PostgreSQL (structure), Redis (session/cache)
- **Validation:** Pydantic v2 (source of truth para schemas)
- **Frontend (optional):** Chat UI

## Project Structure

```
/
├── backend/
│   ├── main.py                  # FastAPI entrypoint
│   ├── api/                     # Route handlers
│   │   ├── __init__.py
│   │   └── routes.py            # generate-ui, iterate-ui, design-system
│   ├── agents/                  # LangGraph agent definitions
│   │   ├── __init__.py
│   │   ├── interpreter.py       # Input Interpreter
│   │   ├── planner.py           # Design Planner
│   │   ├── decomposer.py       # Screen Decomposer (new)
│   │   ├── ux_structurer.py     # UX Structuring
│   │   ├── ui_generator.py      # UI Generator
│   │   ├── mapper.py            # Design System Mapper
│   │   └── validator.py         # Validation Agent
│   ├── orchestrator/            # LangGraph graph & state
│   │   ├── __init__.py
│   │   ├── graph.py             # StateGraph definition
│   │   └── state.py             # Pipeline state model
│   ├── design_system/           # Design system data (underscore, not hyphen)
│   │   ├── __init__.py
│   │   ├── tokens.json
│   │   ├── components.json
│   │   └── rules.json
│   ├── llm/                     # LLM provider abstraction
│   │   ├── __init__.py
│   │   └── provider.py
│   ├── config.py                # pydantic-settings config
│   └── tests/
│       ├── __init__.py
│       ├── test_agents/
│       ├── test_api/
│       └── test_orchestrator/
├── figma-plugin/
│   ├── src/
│   │   ├── renderer.ts
│   │   ├── componentMapper.ts
│   │   └── nodeFactory.ts
│   ├── package.json
│   └── tsconfig.json
├── schemas/                     # Shared — consumed by backend AND plugin
│   └── ui-schema.json
├── CLAUDE.md
├── ARCHITECTURE.md
├── BACKLOG.md
├── pyproject.toml
├── .env.example
└── Justfile
```

## Key Conventions

- All UI output MUST follow `schemas/ui-schema.json` — no free-form generation
- No component is generated outside the design system
- No direct LLM → Figma calls; always pass through validation layer
- Agents communicate via **Pydantic models**, never raw dicts
- UI JSON Schema is auto-generated from Pydantic via `model.model_json_schema()`
- Use LangGraph `StateGraph` for orchestration (not raw chains)
- Schema at `/schemas/` is the single source of truth for both Python and TypeScript

## Agent Pipeline Order

```
Input Interpreter → Design Planner → Screen Decomposer → UX Structuring → UI Generator → Design System Mapper → Validation
```

- Each agent is a LangGraph node
- On failure: retry 2x → fallback to partial output → notify user
- Supports branching and partial re-execution via `/iterate-ui`

## API Endpoints

- `POST /generate-ui` — full pipeline from prompt to UI JSON
- `POST /iterate-ui` — partial re-run with user feedback
- `GET /design-system` — return active design system

## Development Commands

```bash
just dev          # uvicorn backend.main:app --reload
just test         # pytest backend/tests/ -v
just lint         # ruff check backend/
just format       # ruff format backend/
just schema       # generate TypeScript types from ui-schema.json
just plugin-build # cd figma-plugin && npm run build
```

## Code Style

- **Python:** ruff (linter + formatter), type hints obrigatórios em todas as funções
- **TypeScript:** strict mode, prettier
- Docstrings apenas em funções públicas de agents e API endpoints
- Commits em inglês, conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`

## Design Decisions

| Decision | Rationale |
|---|---|
| LangGraph over CrewAI/AutoGen | Fine-grained flow control, native retries, branching |
| Figma Plugin (not REST API) | Lower latency, direct node access |
| Schema as contract | Decouples agents from renderer |
| Pydantic as source of truth | Runtime validation + auto JSON Schema generation |
| Shared /schemas at root | One schema, two languages (Python + TS) |
| Screen Decomposer agent | Separates decomposition from UX structuring (SRP) |
| LLM Provider abstraction | Swap Gemini/Claude/GPT without changing agent code |

## Error Handling

- Agent failure: retry 2x → partial output fallback → user notification
- Schema validation: Pydantic `ValidationError` with clear field-level messages
- API errors: structured JSON error responses with error codes
- Pipeline state is persisted — can resume from last successful agent

## Environment Variables

See `.env.example` for required variables. Managed via `pydantic-settings`.
