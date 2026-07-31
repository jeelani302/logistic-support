"""
models.py — Pydantic schemas for request and response.

Pydantic validates data automatically. If a required field is missing,
FastAPI will return a clear error instead of crashing silently.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


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


class Hypothesis(BaseModel):
    """A possible cause, explicitly separated from verified facts."""

    statement: str = Field(description="A plausible cause that still needs verification.")
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]


class RCAResponse(BaseModel):
    """Evidence-aware analysis that does not present guesses as facts."""

    tracking_id: str = Field(
        description="Package / shipment tracking ID extracted from the ticket. 'N/A' if not found."
    )
    location: str = Field(
        description="Hub, city, or geographic location mentioned in the ticket."
    )
    issue_type: str = Field(
        description="Short label for the problem, e.g. 'Weather Delay', 'Webhook Failure'."
    )
    incident_summary: str
    observed_facts: List[str] = Field(min_length=1)
    hypotheses: List[Hypothesis]
    missing_evidence: List[str]
    recommended_actions: List[str] = Field(min_length=1)
    prevention_measures: List[str]
    draft_support_response: str = Field(
        description="Professional reply that avoids claiming unverified causes."
    )
    overall_confidence: Literal["low", "medium", "high"]


class WebhookTicketRequest(BaseModel):
    """Generic payload for ticketing and logistics webhook integrations."""

    raw_text: Optional[str] = Field(default=None, min_length=10, max_length=10_000)
    source: str = Field(default="generic", max_length=100)
    event_id: Optional[str] = Field(default=None, max_length=200)
    ticket: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def require_ticket_content(self):
        if not self.raw_text and not self.ticket:
            raise ValueError("Provide raw_text or a ticket object.")
        return self

    def to_raw_text(self) -> str:
        if self.raw_text:
            return self.raw_text

        assert self.ticket is not None
        preferred_fields = (
            "id", "subject", "description", "body", "status", "priority",
            "error_code", "tracking_id", "location",
        )
        lines = [f"Source: {self.source}"]
        if self.event_id:
            lines.append(f"Event ID: {self.event_id}")
        for field in preferred_fields:
            value = self.ticket.get(field)
            if value not in (None, ""):
                lines.append(f"{field.replace('_', ' ').title()}: {value}")
        if len(lines) <= 2:
            lines.append(f"Ticket payload: {self.ticket}")
        return "\n".join(lines)[:10_000]
