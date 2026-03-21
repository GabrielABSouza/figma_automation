# Backlog — Figma Automation Pipeline

> Organizado por épicos com prioridade e status. Tasks marcadas com `[MVP]` são escopo mínimo.

---

## Epic 1: Foundation & Infrastructure

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 1.1 | Setup Python project com pyproject.toml e dependências | P0 | done | MVP |
| 1.2 | Configurar `pydantic-settings` com `.env` | P0 | done | MVP |
| 1.3 | Criar FastAPI app com endpoints stub | P0 | done | MVP |
| 1.4 | Definir Pydantic models (PipelineState e sub-models) | P0 | done | MVP |
| 1.5 | Criar design system base (tokens, components, rules) | P0 | done | MVP |
| 1.6 | Criar UI JSON Schema compartilhado em `/schemas` | P0 | done | MVP |
| 1.7 | Configurar ruff + pytest | P1 | todo | MVP |
| 1.8 | Configurar pre-commit hooks | P2 | todo | Post-MVP |

---

## Epic 2: LLM Provider Abstraction

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 2.1 | Implementar `LLMProvider` protocol | P0 | done | MVP |
| 2.2 | Implementar `GeminiProvider` (Gemini) | P0 | done | MVP |
| 2.3 | Implementar `OpenAIProvider` (GPT fallback) | P2 | todo | Post-MVP |
| 2.4 | Criar structured output via Pydantic (response_schema nativo) | P0 | done | MVP |
| 2.5 | Implementar retry logic com exponential backoff | P1 | done | MVP |
| 2.6 | Implementar `AnthropicProvider` (Claude fallback) | P2 | todo | Post-MVP |

---

## Epic 3: Agent Pipeline (Core)

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 3.1 | Implementar Input Interpreter agent | P1 | todo | Post-MVP |
| 3.2 | Implementar Design Planner agent | P0 | done | MVP |
| 3.3 | Implementar Screen Decomposer agent | P2 | todo | Post-MVP |
| 3.4 | Implementar UX Structurer agent | P1 | todo | Post-MVP |
| 3.5 | Implementar UI Generator agent | P0 | done | MVP |
| 3.6 | Implementar Design System Mapper agent | P0 | done | MVP |
| 3.7 | Implementar Validation Agent | P0 | done | MVP |
| 3.8 | Criar prompts otimizados para cada agent | P0 | done | MVP |

---

## Epic 4: LangGraph Orchestration

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 4.1 | Definir StateGraph com nodes e edges | P0 | todo | MVP |
| 4.2 | Implementar pipeline MVP (Planner → UIGen → Mapper → Validator) | P0 | todo | MVP |
| 4.3 | Adicionar retry por node (2x) | P1 | todo | MVP |
| 4.4 | Implementar pipeline completa (todos os 7 agents) | P1 | todo | Post-MVP |
| 4.5 | Adicionar conditional branching e partial execution | P2 | todo | Post-MVP |
| 4.6 | State persistence para resume de pipeline | P2 | todo | Post-MVP |

---

## Epic 5: API Layer

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 5.1 | Implementar `POST /generate-ui` com pipeline real | P0 | todo | MVP |
| 5.2 | Implementar `GET /design-system` | P1 | todo | MVP |
| 5.3 | Implementar `POST /iterate-ui` com feedback loop | P2 | todo | Post-MVP |
| 5.4 | Adicionar request/response models com validação | P1 | todo | MVP |
| 5.5 | Error handling padronizado (error codes, messages) | P1 | todo | MVP |
| 5.6 | Rate limiting e autenticação básica | P2 | todo | Post-MVP |

---

## Epic 6: Figma Plugin

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 6.1 | Setup projeto TypeScript do plugin | P0 | todo | MVP |
| 6.2 | Implementar `componentMapper.ts` (JSON type → Figma component) | P0 | todo | MVP |
| 6.3 | Implementar `nodeFactory.ts` (create Figma nodes) | P0 | todo | MVP |
| 6.4 | Implementar `renderer.ts` (orchestrate rendering) | P0 | todo | MVP |
| 6.5 | Suporte a frame, text e card (MVP components) | P0 | todo | MVP |
| 6.6 | Gerar tipos TS automaticamente do ui-schema.json | P1 | todo | MVP |
| 6.7 | Suporte a todos os components do design system | P1 | todo | Post-MVP |
| 6.8 | UI do plugin para input e feedback | P2 | todo | Post-MVP |

---

## Epic 7: Testing

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 7.1 | Testes unitários dos Pydantic models | P1 | todo | MVP |
| 7.2 | Testes dos agents com mock LLM | P1 | todo | MVP |
| 7.3 | Testes da pipeline LangGraph (integration) | P1 | todo | MVP |
| 7.4 | Testes dos API endpoints | P1 | todo | MVP |
| 7.5 | Testes do Validation Agent contra design system | P0 | todo | MVP |
| 7.6 | E2E test: prompt → UI JSON válido | P1 | todo | Post-MVP |

---

## Epic 8: Database & Persistence (Post-MVP)

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 8.1 | Setup PostgreSQL + SQLAlchemy models | P2 | todo | Post-MVP |
| 8.2 | Setup Redis para session cache | P2 | todo | Post-MVP |
| 8.3 | Persistir pipeline runs e resultados | P2 | todo | Post-MVP |
| 8.4 | Histórico de iterações por sessão | P3 | todo | Post-MVP |

---

## Epic 9: Feedback Loop (Post-MVP)

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 9.1 | Implementar capture de feedback do Figma | P2 | todo | Post-MVP |
| 9.2 | Re-execução parcial do pipeline com feedback | P2 | todo | Post-MVP |
| 9.3 | AI Critique Agent (UX quality, spacing, hierarchy) | P3 | todo | Post-MVP |

---

## Epic 10: Future Enhancements

| # | Task | Priority | Status | Scope |
|---|------|----------|--------|-------|
| 10.1 | Design → Code (React export) | P3 | todo | Future |
| 10.2 | Multi-theme support | P3 | todo | Future |
| 10.3 | Design system auto-generation from Figma files | P3 | todo | Future |
| 10.4 | A/B UI generation | P3 | todo | Future |
| 10.5 | Live data binding | P3 | todo | Future |
| 10.6 | Frontend Chat UI | P3 | todo | Future |

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| P0 | Blocker — must be done for MVP to work |
| P1 | Important — MVP quality/stability |
| P2 | Nice to have — post-MVP first wave |
| P3 | Future — roadmap items |

## Status Legend

| Status | Meaning |
|--------|---------|
| done | Completed |
| in-progress | Being worked on |
| todo | Not started |
| blocked | Waiting on dependency |

---

## Suggested MVP Execution Order

```
1. Epic 2 (LLM Provider)     → foundation for all agents
2. Epic 3 (Agents: 3.2, 3.5, 3.6, 3.7, 3.8) → core pipeline
3. Epic 4 (Orchestration: 4.1, 4.2, 4.3)     → wire agents
4. Epic 5 (API: 5.1, 5.4, 5.5)               → expose via HTTP
5. Epic 6 (Plugin: 6.1–6.6)                   → render in Figma
6. Epic 7 (Tests: 7.1–7.5)                    → validate everything
```
