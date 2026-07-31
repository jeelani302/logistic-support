"""
main.py — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload

Then visit http://localhost:8000/docs for the interactive API explorer.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.demo_logs import generate_demo_log, get_demo_logs
from app.llm_client import analyze_ticket
from app.models import RCAResponse, TicketRequest, WebhookTicketRequest

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
    version="2.0.0",
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


@app.get("/demo-logs", tags=["Demo"])
def list_demo_logs():
    """Return synthetic incidents that are safe to use in demos."""
    return {"logs": get_demo_logs()}


@app.post("/demo-logs/generate", tags=["Demo"])
def create_demo_log():
    """Select a synthetic incident without consuming LLM quota."""
    return generate_demo_log()


def _analyze(raw_text: str) -> RCAResponse:
    """Run analysis with consistent, non-sensitive error handling."""
    try:
        result = analyze_ticket(raw_text)
        return RCAResponse(**result)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("Provider returned invalid structured output: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The AI response could not be validated. Please retry the analysis.",
        ) from exc
    except Exception as exc:
        logger.exception("Ticket analysis failed")
        raise HTTPException(
            status_code=503,
            detail="The analysis service is temporarily unavailable. Please try again.",
        ) from exc


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
    - observed facts separated from hypotheses
    - missing evidence and confidence labels
    - recommended actions and prevention measures
    - a customer reply that avoids unverified claims
    """
    return _analyze(request.raw_text)


@app.post(
    "/webhooks/ticket",
    response_model=RCAResponse,
    tags=["Integrations"],
    summary="Analyze a ticket submitted by an external system",
)
def analyze_webhook_ticket(
    request: WebhookTicketRequest,
    x_webhook_secret: str | None = Header(default=None),
):
    """Accept generic Zendesk/Freshdesk-style ticket fields securely."""
    configured_secret = os.getenv("WEBHOOK_SECRET")
    if not configured_secret:
        raise HTTPException(status_code=503, detail="Webhook integration is not configured.")
    if x_webhook_secret != configured_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")
    return _analyze(request.to_raw_text())
