# Architecture — AI Figma Generation Pipeline

## Overview

This system converts **product intent (PRD, prompt, or chat input)** into **structured UI screens rendered directly in Figma**, using a **multi-agent architecture** and a **design system as constraint engine**.

The pipeline is deterministic, extensible, and designed for **production-grade UI generation**, not just prototyping.

---

## High-Level Architecture

```
[User Input / PRD / Chat]
            ↓
[API Layer - FastAPI]
            ↓
[Multi-Agent Design Engine (LangGraph)]
            ↓
[Pydantic Models → UI JSON Schema]
            ↓
[Figma Renderer (Plugin)]
            ↓
[Figma File (Screens / Components)]
            ↓
[Feedback Loop → Iteration]
```

---

## Core Components

### 1. Design System Layer

**Responsibility:**
Acts as the constraint engine for UI generation.

**Includes:**

* Design tokens (colors, spacing, typography)
* Component definitions (variants, props)
* Layout rules (grid, padding, hierarchy)

**Structure:**

```
backend/design_system/
  ├── __init__.py
  ├── tokens.json
  ├── components.json
  └── rules.json
```

> **Decision:** Uses `design_system` (underscore) instead of `design-system` (hyphen) for Python import compatibility.

**Key Principle:**

> No UI is generated outside the design system.

---

### 2. Multi-Agent Design Engine

**Stack:**

* Python 3.12+
* LangGraph (StateGraph)
* LLM via provider abstraction (Claude primary, GPT fallback)

**Responsibility:**
Transforms user intent into structured UI definitions via Pydantic models.

---

## Agent Pipeline

```
[Input Interpreter]
        ↓
[Design Planner Agent]
        ↓
[Screen Decomposer Agent]    ← NEW: separates decomposition from structuring
        ↓
[UX Structuring Agent]
        ↓
[UI Generator Agent]
        ↓
[Design System Mapper]
        ↓
[Validation Agent]
```

---

### Agent Definitions

#### 1. Input Interpreter

* Parses user input (chat, PRD, URL, etc.)
* Extracts:
  * product type
  * user goals
  * required screens
* **Output:** `InterpretedInput` Pydantic model

---

#### 2. Design Planner Agent

* Defines:
  * list of screens
  * navigation flow
* **Output:** `DesignPlan` Pydantic model

```json
{
  "screens": [
    { "name": "Login", "purpose": "authentication", "priority": 1 },
    { "name": "Dashboard", "purpose": "main overview", "priority": 2 }
  ],
  "navigation_flow": ["Login", "Dashboard", "Details"]
}
```

---

#### 3. Screen Decomposer Agent (NEW)

* Decomposes each screen into atomic sections
* Defines section boundaries and content types
* **Rationale:** Follows SRP — separates screen decomposition from UX structuring
* **Output:** `DecomposedScreens` Pydantic model

---

#### 4. UX Structuring Agent

* Defines layout hierarchy per screen (using decomposed sections as input)
* Assigns priorities and spatial relationships
* **Output:** `UXStructure` Pydantic model

---

#### 5. UI Generator Agent

* Generates raw UI tree (layout-first, not styled)
* **Output:** `RawUITree` Pydantic model

---

#### 6. Design System Mapper

* Maps abstract UI → real components
* Applies tokens and variants
* **Output:** `MappedUI` Pydantic model

---

#### 7. Validation Agent

* Ensures:
  * schema validity (Pydantic validation)
  * component existence in design system
  * token consistency
  * layout coherence
* **Output:** `ValidatedUI` Pydantic model (final output)

> **Decision:** Validation Agent is included in MVP scope — it's the enforcement mechanism for "no component outside design system".

---

## Schema Strategy

### Pydantic as Source of Truth

All agents communicate via **Pydantic models**. The shared JSON Schema is auto-generated:

```python
# Generate JSON Schema from Pydantic
schema = ValidatedUI.model_json_schema()
```

### Shared Schema Location

```
/schemas/ui-schema.json    ← auto-generated from Pydantic, consumed by both Python and TypeScript
```

> **Decision:** Schema lives at project root (not inside `/backend`), because the Figma plugin also consumes it. TypeScript types are auto-generated via `json-schema-to-typescript`.

### Base Structure

```json
{
  "screen": "string",
  "layout": [
    {
      "type": "section",
      "children": []
    }
  ],
  "components": [
    {
      "id": "string",
      "type": "card",
      "props": {},
      "tokens": {}
    }
  ],
  "tokens": {},
  "metadata": {
    "schema_version": "1.0.0"
  }
}
```

> **Decision:** Schema is versioned via `metadata.schema_version` to prevent silent breakage between backend and plugin.

---

## API Layer (FastAPI)

**Responsibilities:**

* Receive user input
* Trigger agent pipeline
* Return structured UI JSON (validated Pydantic → JSON)
* Send data to Figma Renderer

---

### Endpoints

#### POST /generate-ui

Input:

```json
{
  "prompt": "SaaS dashboard for financial tracking"
}
```

Output:

```json
{
  "screens": [...],
  "metadata": {
    "schema_version": "1.0.0",
    "pipeline_run_id": "uuid"
  }
}
```

---

#### POST /iterate-ui

* Accepts feedback + previous `pipeline_run_id`
* Re-runs partial pipeline from the appropriate agent

---

#### GET /design-system

* Returns active design system (tokens, components, rules)

---

## Figma Renderer Layer

### Figma Plugin (Chosen for MVP)

> **Decision:** Plugin over REST API for lower latency and direct Figma node access.

**Responsibilities:**

* Receive UI JSON
* Map to Figma nodes
* Create frames, components, text layers

**Structure:**

```
figma-plugin/
  ├── src/
  │   ├── renderer.ts
  │   ├── componentMapper.ts
  │   └── nodeFactory.ts
  ├── package.json
  └── tsconfig.json
```

---

### Rendering Flow

```
UI JSON (validated)
  ↓
Component Mapper (JSON type → Figma component)
  ↓
Node Factory (create Figma nodes)
  ↓
Figma Nodes (rendered)
```

---

### Core Functions

```ts
function renderScreen(screen: Screen): FrameNode {}
function createComponent(node: UIComponent): SceneNode {}
function applyTokens(node: SceneNode, tokens: DesignTokens): void {}
```

---

## Feedback Loop

### Types

#### 1. User Feedback

* Edits in Figma
* Sends updates back via `/iterate-ui`

#### 2. AI Critique Agent (Post-MVP)

* Evaluates:
  * UX quality
  * spacing consistency
  * hierarchy clarity

#### 3. Iterative Refinement

```
Generate → Validate → Improve → Render
```

---

## Error Handling Strategy

| Scenario | Behavior |
|---|---|
| Agent failure | Retry 2x → fallback to partial output → notify user |
| Schema validation error | Pydantic `ValidationError` with field-level messages |
| API error | Structured JSON error response with error code |
| Pipeline interruption | State is persisted — resume from last successful agent |

---

## State Management

Use persistent storage for:

* Generated screens
* User sessions
* Pipeline iterations and state

**Stack:**

* PostgreSQL (structure, pipeline history)
* Redis (session cache, rate limiting)

---

## LLM Provider Abstraction

> **Decision:** Abstract LLM calls behind a provider interface to avoid vendor lock-in.

```python
class LLMProvider(Protocol):
    async def generate(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...
```

* **Primary:** Claude (Anthropic SDK)
* **Fallback:** GPT (OpenAI SDK)
* Swap providers without changing agent code

---

## Configuration Management

> **Decision:** Use `pydantic-settings` with `.env` for all secrets and configuration.

Required environment variables:
* `ANTHROPIC_API_KEY` — Claude API access
* `OPENAI_API_KEY` — GPT fallback (optional)
* `FIGMA_ACCESS_TOKEN` — Figma API access
* `DATABASE_URL` — PostgreSQL connection
* `REDIS_URL` — Redis connection

See `.env.example` for full list.

---

## Folder Structure

```
/
├── backend/
│   ├── main.py
│   ├── config.py                # pydantic-settings
│   ├── api/
│   ├── agents/
│   ├── orchestrator/
│   ├── design_system/           # underscore for Python imports
│   ├── llm/                     # provider abstraction
│   └── tests/
├── figma-plugin/
│   └── src/
├── schemas/                     # shared root — consumed by backend AND plugin
│   └── ui-schema.json
├── frontend/ (optional)
│   └── chat-ui/
├── CLAUDE.md
├── ARCHITECTURE.md
├── BACKLOG.md
├── pyproject.toml
├── .env.example
└── Justfile
```

---

## Orchestration (LangGraph)

Each agent is a node in a `StateGraph`.

```
START
  → Input Interpreter
  → Planner
  → Screen Decomposer
  → UX Structurer
  → UI Generator
  → Mapper
  → Validator
END
```

Supports:

* retries (2x per node)
* conditional branching
* partial execution (resume from any node)
* state persistence between runs

---

## Constraints & Rules

1. No component outside design system
2. All agent outputs must be Pydantic models following the schema
3. No direct LLM → Figma calls
4. Always pass through validation layer
5. Schema is versioned — breaking changes require version bump
6. All secrets managed via `.env` / `pydantic-settings`

---

## MVP Scope

**Include:**

* 4 agents: Planner + UI Generator + Mapper + **Validator**
* Pydantic models + auto-generated JSON Schema
* Figma plugin (frame + text + card)
* Basic error handling (retry 2x)
* `.env` config management

> **Decision change:** Validator is now included in MVP — it enforces the core constraint ("no component outside design system").

**Exclude (for now):**

* Full feedback loop (POST /iterate-ui)
* Advanced critique agent
* Real-time collaboration
* Screen Decomposer agent (UX Structurer handles both in MVP)
* Frontend chat UI

---

## Future Enhancements

* Design → Code (React export)
* Live data binding
* Multi-theme support
* Design system auto-generation from Figma files
* A/B UI generation
* Screen Decomposer agent (split from UX Structurer)
* AI Critique Agent for automated UX review

---

## Guiding Principle

> This is not "AI generating screens".
> This is a **deterministic design system pipeline powered by AI agents**.

---

## Final Goal

Input:

```
"Build a fintech dashboard for SMBs"
```

Output:

* Structured UI (validated Pydantic models)
* Fully rendered Figma screens
* Consistent with design system
* Ready for handoff or code generation
