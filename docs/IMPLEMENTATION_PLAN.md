# Project Hydra — Advanced Capability Implementation Plan

## Current Test Coverage Assessment

The repository currently has no automated tests for the FastAPI orchestration flow, security guardrails, or endpoint behavior. Coverage gaps observed:

1. **Core helper logic untested**
   - `security_scan()` pattern enforcement
   - `build_prompt()` prompt contract
2. **API contract untested**
   - `GET /` status and metric aggregation
   - `GET /log` retention behavior (last 50 entries)
   - `POST /evolve` happy-path and error-path responses
3. **Safety/error handling untested**
   - Invalid JSON payload handling
   - Missing field validation
   - AI synthesis failure handling
   - Banned output rejection handling

## What Was Added in This Iteration

- A focused pytest suite for the backend orchestration (`tests/test_brain.py`) that validates success, failure, and rejection flows with AI client stubbing.
- Vercel deployment scaffolding (`vercel.json`, `api/index.py`) to support static UI hosting + Python API function routing.

## Detailed Roadmap for Advanced Capabilities

### Phase 1 — Reliability and Test Maturity (Immediate)

- Add `pytest-cov` and enforce minimum branch coverage in CI.
- Add regression tests for log truncation + response schema consistency.
- Add property-based fuzz tests for `security_scan` bypass attempts.
- Add request/response schema models (Pydantic) to tighten API contracts.

### Phase 2 — Security Hardening

- Move from regex-only scanning to AST-based JS policy checks.
- Add signed patch envelopes (HMAC) between Brain and workers.
- Add per-worker auth tokens and replay-protection nonces.
- Add configurable policy tiers (strict/moderate/dev mode).

### Phase 3 — Observability and Operations

- Add structured tracing (OpenTelemetry) for each evolution phase.
- Export metrics to Prometheus (latency, rejection rate, AI failure rate).
- Add audit persistence (SQLite/Postgres) rather than in-memory-only logs.
- Add circuit-breaker behavior for repeated upstream AI failures.

### Phase 4 — Multi-Model Intelligence

- Add model router with policy-driven fallback (DeepSeek → Groq/Ollama).
- Introduce prompt templates per error class (TypeError, async race, parsing).
- Add patch scoring (safety + performance + confidence) before delivery.
- Add offline simulation harness for comparing model quality/cost/latency.

### Phase 5 — Vercel-Ready Production Deployment

- Finalize Vercel environment variables:
  - `DEEPSEEK_API_KEY`
  - `BASE_URL`
  - `MODEL`
- Add `vercel.json` rewrite/route tests in preview deploys.
- Add edge caching headers for static assets.
- Add API timeout and retry strategy tuned for serverless runtime limits.

### Phase 6 — Good Mobile Responsive UI

- Audit all dashboard layouts at 320px, 375px, 768px breakpoints.
- Prioritize mobile nav ergonomics:
  - collapsible sidebar
  - sticky action bar for “Run Simulation”
  - large touch targets
- Reduce chart density and non-critical widgets on narrow screens.
- Add visual regression checks for mobile (Playwright screenshot diff).

### Phase 7 — Product Extensions (Advanced)

- Worker fleet management:
  - per-region health map
  - canary patch rollout
  - rollback dashboard
- Knowledge memory:
  - cluster errors by signature
  - recommend known-good patches before AI synthesis
- Governance:
  - human approval mode for high-risk patches
  - immutable patch history + compliance exports

## Suggested CI/CD Plan

1. **PR pipeline**
   - lint + tests + coverage gate
   - static security checks
2. **Preview deployment (Vercel)**
   - run API smoke checks against preview URL
3. **Production promotion**
   - gated by coverage and smoke test pass

## Clarifications Needed Before Full Execution

1. Preferred minimum test coverage target (e.g., 85%, 90%, 95%)?
2. Should Vercel host **only** frontend, while Brain API stays on a long-running host (Render/Fly.io), or do you want everything serverless-first?
3. Do you want mobile responsiveness improvements delivered as a dedicated UI refactor next, or limited to critical-path screens first?
