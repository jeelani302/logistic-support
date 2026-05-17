# Logistics Support & RCA Agent

A FastAPI backend that accepts raw logistics error logs or customer support tickets and returns a structured **Root Cause Analysis (RCA)** report and a draft support response — powered by Google Gemini.

---

## Project Structure

```
logistic-support/
├── .env                  ← Your API key (never committed)
├── .gitignore
├── requirements.txt
├── app/
│   ├── main.py           ← FastAPI app + routes
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
Visit **http://localhost:8000/docs** in your browser. You can test the API directly from there — no extra tools needed.

---

## API Reference

### `GET /`
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
