"""
models.py — Pydantic schemas for request and response.

Pydantic validates data automatically. If a required field is missing,
FastAPI will return a clear error instead of crashing silently.
"""

from pydantic import BaseModel, Field
from typing import List


class TicketRequest(BaseModel):
    """What the caller sends us — just the raw ticket/log text."""

    raw_text: str = Field(
        ...,
        min_length=10,
        max_length=10_000,
        description="Raw support ticket or logistics error log to analyze.",
        examples=[
            "Package ID 4412 delayed at Bangalore hub due to heavy rain, "
            "webhook failed to update status"
        ],
    )


class RCAResponse(BaseModel):
    """Structured output we return after Gemini analysis."""

    tracking_id: str = Field(
        description="Package / shipment tracking ID extracted from the ticket. 'N/A' if not found."
    )
    location: str = Field(
        description="Hub, city, or geographic location mentioned in the ticket."
    )
    issue_type: str = Field(
        description="Short label for the problem, e.g. 'Weather Delay', 'Webhook Failure'."
    )
    root_cause_analysis: List[str] = Field(
        min_length=3,
        max_length=3,
        description="Exactly 3 bullet-point strings explaining the root causes."
    )
    draft_support_response: str = Field(
        description="Professional, empathetic 2-3 sentence reply ready to send to the customer."
    )
