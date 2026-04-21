"""
Project Hydra — Central Brain
==============================
Self-healing distributed agentic infrastructure.

Requirements:
    pip install fastapi uvicorn openai

Run:
    uvicorn brain:app --host 0.0.0.0 --port 8000 --reload

Environment Variables:
    DEEPSEEK_API_KEY  — DeepSeek API key (free tier available at platform.deepseek.com)
    GROQ_API_KEY      — Groq API key as fallback for Llama 3 (free tier at console.groq.com)
    MODEL             — AI model to use (default: deepseek-chat)
    BASE_URL          — API base URL (default: https://api.deepseek.com)

Notes:
    - For local/offline use, point BASE_URL to your Ollama instance:
        BASE_URL=http://localhost:11434/v1  MODEL=llama3
    - The /evolve endpoint implements Phases 2-5 of the Hydra self-correction loop.
"""

import os
import re
import time
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
import uvicorn

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("hydra.brain")

# ── Config ───────────────────────────────────────────────────────────────────

API_KEY  = os.getenv("DEEPSEEK_API_KEY", "YOUR_FREE_DEEPSEEK_KEY")
BASE_URL = os.getenv("BASE_URL",         "https://api.deepseek.com")
MODEL    = os.getenv("MODEL",            "deepseek-chat")

# Security: keywords that trigger patch rejection
BANNED_PATTERNS = [
    r"\beval\s*\(",
    r"\bwindow\.",
    r"\bdocument\.cookie",
    r"\bimportScripts\b",
    r"\bfetch\s*\(",
    r"\bXMLHttpRequest\b",
    r"\bprocess\.env\b",
    r"\brequire\s*\(",
    r"\b__dirname\b",
]

# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Project Hydra — Central Brain",
    description="Self-healing AI orchestrator for distributed edge workers",
    version="1.0.0"
)

# Allow cross-origin requests from the Edge Worker (browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to your domain in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Shared AI client ──────────────────────────────────────────────────────────

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ── In-memory audit log ───────────────────────────────────────────────────────

evolution_log: list[dict] = []

# ── Helpers ───────────────────────────────────────────────────────────────────

def security_scan(code: str) -> Optional[str]:
    """
    Phase 4 — Verification.
    Returns the first matched banned pattern, or None if clean.
    """
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, code):
            return pattern
    return None


def build_prompt(error: str, code: str) -> str:
    return f"""You are an expert JavaScript engineer fixing a runtime error in an edge worker.

ERROR MESSAGE:
{error}

ORIGINAL FAILING FUNCTION (body only):
{code}

TASK:
- Return ONLY the corrected function body (no function signature, no markdown fences).
- Fix the reported error defensively.
- Handle null/undefined values with optional chaining or nullish coalescing.
- Optimize for minimal memory use.
- Do NOT use: eval(), window.*, document.cookie, fetch(), XMLHttpRequest, importScripts.
- Do NOT add comments.
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "system": "Project Hydra — Central Brain",
        "version": "1.0.0",
        "status": "online",
        "evolutions": len([e for e in evolution_log if e["outcome"] == "evolved"]),
        "rejections": len([e for e in evolution_log if e["outcome"] == "rejected"]),
    }


@app.get("/log")
async def get_log():
    """Return the full evolution audit log."""
    return {"log": evolution_log[-50:]}  # Return last 50 entries


@app.post("/evolve")
async def evolve_worker(request: Request):
    """
    Main evolution endpoint.

    Expected JSON body:
        {
            "error": "Cannot read properties of null...",
            "code":  "function(data) { return data.items.map(...); }",
            "worker_id": "W-001"  // optional
        }

    Returns:
        { "status": "evolved",   "logic": "<corrected function body>" }
        { "status": "rejected",  "reason": "<security violation description>" }
        { "status": "error",     "detail": "<internal error message>" }
    """
    t0 = time.time()

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    error_ctx  = data.get("error", "").strip()
    failing_code = data.get("code", "").strip()
    worker_id  = data.get("worker_id", "unknown")

    if not error_ctx or not failing_code:
        raise HTTPException(status_code=400, detail="Both 'error' and 'code' fields are required")

    log.info(f"[{worker_id}] Evolution request — error: {error_ctx[:80]}")

    # ── Phase 3: Synthesis ─────────────────────────────────────────────────
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": build_prompt(error_ctx, failing_code)}],
            max_tokens=512,
            temperature=0.2,
        )
        new_logic = response.choices[0].message.content.strip()

        # Strip markdown fences if model wrapped in them
        new_logic = re.sub(r"^```[a-z]*\n?", "", new_logic)
        new_logic = re.sub(r"\n?```$", "", new_logic).strip()

    except Exception as exc:
        log.error(f"AI synthesis failed: {exc}")
        evolution_log.append({
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_ctx,
            "outcome": "error",
            "duration_ms": int((time.time() - t0) * 1000),
        })
        return JSONResponse({"status": "error", "detail": "AI synthesis failed"}, status_code=502)

    # ── Phase 4: Verification ──────────────────────────────────────────────
    violation = security_scan(new_logic)
    if violation:
        log.warning(f"[{worker_id}] Patch REJECTED — violation: {violation}")
        evolution_log.append({
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_ctx,
            "outcome": "rejected",
            "reason": violation,
            "duration_ms": int((time.time() - t0) * 1000),
        })
        return JSONResponse({
            "status": "rejected",
            "reason": f"Security violation detected: {violation}"
        })

    duration_ms = int((time.time() - t0) * 1000)
    log.info(f"[{worker_id}] Evolution complete in {duration_ms}ms")

    evolution_log.append({
        "worker_id": worker_id,
        "timestamp": datetime.utcnow().isoformat(),
        "error": error_ctx,
        "outcome": "evolved",
        "duration_ms": duration_ms,
    })

    # ── Phase 5: Delivery ──────────────────────────────────────────────────
    return JSONResponse({
        "status":      "evolved",
        "logic":       new_logic,
        "model":       MODEL,
        "duration_ms": duration_ms,
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
