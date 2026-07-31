"""
main.py — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload

Then visit http://localhost:8000/docs for the interactive API explorer.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.llm_client import analyze_ticket
from app.models import RCAResponse, TicketRequest

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Logistics Support & RCA Agent",
    description=(
        "Submit a raw logistics error log or customer support ticket. "
        "Get back a structured Root Cause Analysis report and a ready-to-send "
        "draft support response — powered by Gemini."
    ),
    version="1.0.0",
)

# Allow any frontend (browser, React app, etc.) to call this API
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


STATIC_DIR = Path(__file__).parent / "static"
logger = logging.getLogger(__name__)


@app.get("/", include_in_schema=False)
def home():
    """Serve the browser interface."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["Health"])
def health_check():
    """Deployment health check that does not call the LLM provider."""
    return {"status": "ok", "message": "Logistics RCA Agent is live 🚀"}


@app.post(
    "/analyze-ticket",
    response_model=RCAResponse,
    tags=["RCA"],
    summary="Analyze a support ticket or error log",
    response_description="Structured RCA report with draft support response",
)
def analyze_ticket_endpoint(request: TicketRequest):
    """
    **Submit a raw logistics ticket and get a structured RCA report.**

    **Example input:**
    ```
    Package ID 4412 delayed at Bangalore hub due to heavy rain,
    webhook failed to update status.
    ```

    **What you get back:**
    - `tracking_id` — extracted package ID
    - `location` — hub/city
    - `issue_type` — short label for the problem
    - `root_cause_analysis` — 3-point RCA list
    - `draft_support_response` — ready-to-send customer reply
    """
    try:
        result = analyze_ticket(request.raw_text)
    except EnvironmentError as exc:
        # API key not configured
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        # Gemini returned bad/incomplete JSON
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        # Any other unexpected error (network, quota, etc.)
        logger.exception("Ticket analysis failed")
        raise HTTPException(
            status_code=503,
            detail="The analysis service is temporarily unavailable. Please try again.",
        ) from exc

    # Pydantic validates that `result` matches RCAResponse before returning
    return RCAResponse(**result)
