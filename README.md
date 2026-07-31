# Logistics Support & RCA Agent

[![Live Demo](https://img.shields.io/badge/Live_Demo-Open_App-46E3B7?style=for-the-badge)](https://logistics-rca-agent.onrender.com)

**Live application:** https://logistics-rca-agent.onrender.com

A deployable FastAPI app with a browser interface. It turns logistics error logs and support tickets into an evidence-aware incident investigation — powered by Google Gemini.

Unlike a basic log summarizer, the agent separates **observed facts** from **unverified hypotheses**, identifies missing evidence, recommends recovery actions, proposes prevention measures, and drafts a customer response that does not overclaim.

> AI-generated analysis can be inaccurate. Review every RCA and response before using it operationally, and do not submit secrets or sensitive customer data.

---

## Project Structure

```
logistic-support/
├── .env                  ← Your API key (never committed)
├── .gitignore
├── requirements.txt
├── app/
│   ├── main.py           ← FastAPI app + routes
│   ├── static/index.html  ← Browser interface
│   ├── models.py         ← Pydantic input/output schemas
│   ├── llm_client.py     ← Gemini API logic
│   └── prompts.py        ← System prompt template
└── README.md
```

---

## Quick Start

### 1. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Gemini API key
Open `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_real_key_here
```
Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 4. Run the server
```bash
uvicorn app.main:app --reload
```

### 5. Open the interactive docs
Visit **http://localhost:8000** for the browser app or **http://localhost:8000/docs** for the interactive API documentation.

The browser includes a sample selector and a **Generate demo log** button. All bundled incidents are synthetic and generating one does not call Gemini or consume API quota.

## Free deployment on Render

The current deployment is available at **[logistics-rca-agent.onrender.com](https://logistics-rca-agent.onrender.com)**.

This repository includes a `Dockerfile` and `render.yaml` blueprint.

1. Fork or push this repository to your GitHub account.
2. In Render, choose **New → Blueprint** and connect the repository.
3. Render detects `render.yaml`. Enter `GEMINI_API_KEY` when prompted and create the service.
4. Wait for the health check at `/health` to pass, then open the generated `onrender.com` URL.

The blueprint selects Render's free web-service plan. Free services sleep after inactivity, so the first request after idle can take about a minute. The Gemini model defaults to `gemini-3.5-flash-lite`, which currently has a limited free API tier. Never commit the API key.

## Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## API Reference

### `GET /health`
Health check.

```json
{ "status": "ok", "message": "Logistics RCA Agent is live 🚀" }
```

### `POST /analyze-ticket`

**Request body:**
```json
{
  "raw_text": "Package ID 4412 delayed at Bangalore hub due to heavy rain, webhook failed to update status"
}
```

**Response fields:**
```json
{
  "tracking_id": "4412",
  "location": "Bangalore hub",
  "issue_type": "Weather delay and webhook failure",
  "incident_summary": "Shipment and notification updates are delayed.",
  "observed_facts": ["The ticket reports heavy rain and a failed webhook."],
  "hypotheses": [
    {
      "statement": "Weather may have interrupted hub operations.",
      "supporting_evidence": ["Heavy rain was reported at the hub."],
      "confidence": "medium"
    }
  ],
  "missing_evidence": ["Hub scan history", "Webhook response and retry logs"],
  "recommended_actions": ["Inspect the latest hub scans.", "Check and replay the webhook event safely."],
  "prevention_measures": ["Alert on shipment and customer-status divergence."],
  "draft_support_response": "We are investigating the shipment delay and will provide an update shortly.",
  "overall_confidence": "medium"
}
```

### Ticket-system webhook

`POST /webhooks/ticket` accepts either `raw_text` or common fields inside a `ticket` object. On Render, `WEBHOOK_SECRET` is generated automatically. Send that value in the `X-Webhook-Secret` header.

```bash
curl -X POST http://localhost:8000/webhooks/ticket \
  -H 'Content-Type: application/json' \
  -H 'X-Webhook-Secret: your-secret' \
  -d '{
    "source": "zendesk",
    "event_id": "evt-123",
    "ticket": {
      "id": "9081",
      "subject": "Tracking not updated",
      "description": "Package PKG-18 departed Delhi but tracking still shows Processing",
      "priority": "high"
    }
  }'
```

Configure Zendesk, Freshdesk, Jira, or another platform to send JSON to the deployed `/webhooks/ticket` URL and include the secret header. Map the platform's ticket description into either `raw_text` or `ticket.description`.

---

## Security Note

Your API key lives only in `.env`, which is listed in `.gitignore`. It will **never** be pushed to GitHub.
