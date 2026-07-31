# Logistics Support & RCA Agent

A deployable FastAPI app with a browser interface. It accepts raw logistics error logs or customer support tickets and returns a structured **Root Cause Analysis (RCA)** report and a draft support response — powered by Google Gemini.

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

## Free deployment on Render

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

**Response:**
```json
{
  "tracking_id": "4412",
  "location": "Bangalore hub",
  "issue_type": "Weather Delay + Webhook Failure",
  "root_cause_analysis": [
    "Heavy rainfall caused physical congestion at the Bangalore hub, halting outbound shipments.",
    "The webhook integration lacked a retry mechanism, causing it to silently fail on the first attempt.",
    "No alerting was triggered to notify the operations team of the missed status update."
  ],
  "draft_support_response": "Dear Customer, we sincerely apologize for the delay with your package #4412. Severe weather conditions at our Bangalore hub have caused temporary disruptions, and our team is actively working to resume normal operations. We will keep you updated as soon as your shipment is on its way."
}
```

---

## Security Note

Your API key lives only in `.env`, which is listed in `.gitignore`. It will **never** be pushed to GitHub.
