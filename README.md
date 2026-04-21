# ⬡ Project Hydra
### Distributed Agentic Infrastructure — Self-Healing Edge Workers

> **Thesis project** by John Rish Ladica  
> BS Information Technology · Southern Leyte State University – Hinunangan Campus

---

## Overview

Project Hydra is a distributed system where edge workers **self-heal at runtime** when they encounter logic failures — without human intervention.

When a worker crashes, it:
1. Captures the error and failing code
2. POSTs a telemetry payload to the Central Brain
3. The Brain synthesizes a fix using AI (DeepSeek-V3 / Llama 3)
4. The fix is verified for security violations
5. Delivered as a JSON string (~1.2 KB vs ~7 MB for a full update)
6. Injected at runtime via `new Function()` — the worker heals itself

**Result:** Mean Time To Repair drops from hours → milliseconds.  
**Bandwidth reduction:** 5.9× vs traditional firmware/app bundle updates.

---

## Files

| File | Description |
|------|-------------|
| `index.html` | Full dashboard UI (FineStyle 3.0) — open this in a browser |
| `brain.py` | Central Brain FastAPI server — run this to enable live healing |
| `edge-worker.html` | Standalone edge worker demo — connects to brain.py |
| `fs-3.0.min.css` | FineStyle 3.0 stylesheet |
| `fs-3.0.min.js` | FineStyle 3.0 engine |

---

## Quick Start

### 1. Dashboard (no server needed)
```
Open index.html in any browser.
```
The dashboard includes a full built-in simulation — no backend required.

### 2. Full System (with live AI healing)

**Install dependencies:**
```bash
pip install fastapi uvicorn openai
```

**Set your API key:**
```bash
# Free key from: https://platform.deepseek.com
export DEEPSEEK_API_KEY="your_key_here"

# Or use Groq (free Llama 3):
export BASE_URL="https://api.groq.com/openai/v1"
export DEEPSEEK_API_KEY="your_groq_key"
export MODEL="llama-3.3-70b-versatile"

# Or run fully offline with Ollama:
export BASE_URL="http://localhost:11434/v1"
export DEEPSEEK_API_KEY="ollama"
export MODEL="llama3"
```

**Start the Brain:**
```bash
python brain.py
# or: uvicorn brain:app --reload --port 8000
```

**Open the edge worker:**
```
Open edge-worker.html in your browser.
Click "Run Task" to trigger the self-correction loop.
```

---

## The Six-Phase Loop

| Phase | Name | Component | Description |
|-------|------|-----------|-------------|
| ① | **Failure** | Edge Worker | Runtime error caught |
| ② | **Telemetry** | Edge → Brain | Error + code sent via POST |
| ③ | **Synthesis** | Central Brain | AI generates corrected logic |
| ④ | **Verification** | Central Brain | Security scan (blocks eval, window.*, etc.) |
| ⑤ | **Delivery** | Brain → Edge | JSON patch (~1.2 KB) returned |
| ⑥ | **Injection** | Edge Worker | `new Function()` replaces old logic |

---

## Security — Execution Ladder

Synthesized code is scanned and escalated through hardened sandboxes:

| Tier | Environment | Use Case |
|------|-------------|----------|
| T1 | JS Isolate | Simple logic patches |
| T2 | Scoped Web Worker | Restricted environment |
| T3 | Shadow iframe + CSP | Isolated execution |
| T4 | Docker container | Full sandboxing |

**Blocked patterns:** `eval()`, `window.*`, `document.cookie`,  
`fetch()`, `XMLHttpRequest`, `require()`, `process.env`

---

## AI Model Selection

| Model | Cost | Accuracy | Notes |
|-------|------|----------|-------|
| **DeepSeek-V3** | ~1× | ★★★★★ | **Recommended** — 32× cheaper than GPT-4o |
| Llama 3.3 70B | Free (Groq) | ★★★★☆ | Great fallback |
| Gemini 2.0 Flash | Free | ★★★★☆ | Google AI Studio |
| GPT-4o | ~32× | ★★★★★ | Expensive for this use case |

---

## Key Metrics

- **MTTR:** Hours → ~milliseconds  
- **Bandwidth reduction:** 5.9× (JSON patch vs full bundle)  
- **AI cost reduction:** 32× vs closed-source models  
- **Zero-touch debugging:** No human intervention required

---

## Tech Stack

- **Backend:** Python · FastAPI · Uvicorn · OpenAI SDK
- **Frontend:** Vanilla JS · FineStyle 3.0 · Chart.js · Feather Icons
- **AI:** DeepSeek-V3 · Llama 3 · Groq · Ollama (local)

---

*Framework: FineStyle 3.0 by John Rish Ladica*
