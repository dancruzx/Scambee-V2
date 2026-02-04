# Evaluation Readiness Checklist

This document details how **Project ScamBee** meets the core evaluation criteria.

## 1. Reliability (Multiple Requests)
- **Architecture**: Built on **FastAPI**, an asynchronous framework. This allows the server to handle hundreds of concurrent connections (non-blocking I/O) even on a single thread.
- **Concurrency**: We use `uvicorn` with `async/await` for all AI calls. While Gemini is generating a response for User A, the server is free to accept requests from User B.
- **Deployment**: Hosted on **Render**, which automatically manages uptime.
- **Model Fallback**: The `ModelFallbackManager` prevents the system from crashing if the primary AI model is overloaded or hits a rate limit. It automatically tries `gemini-2.5-flash` -> `2.0-flash` -> `2.0-flash-lite`.

## 2. JSON Response Format
The API strictly adheres to the required schema using **Pydantic Models**. The "Agentic Honey-Pot Tester" has verified valid 200 OK responses.

**Schema:**
```json
{
  "is_scam": boolean,
  "confidence_score": float (0.0 - 1.0),
  "generated_reply": string (or null),
  "extracted_intelligence": {
    "upi_ids": [string],
    "bank_accounts": [string],
    "urls": [string]
  },
  "engagement_metrics": {
    "mood": string,
    "turn_count": integer
  }
}
```

## 3. Low Latency
- **Model Selection**: We use `gemini-2.0-flash` and `2.5-flash`, which are Google's fastest models, specifically optimized for sub-second latency.
- **Regex Extraction**: Intelligence extraction (UPI, URLs) is done via Python Regex (ms) rather than waiting for an LLM to do it.
- **Prompt Optimization**: The Guard Agent uses a streamlined "JSON-only" prompt to minimize token generation time.

## 4. Error Handling
- **422 Validation Fix**: Implemented flexible input handling (`message` / `input` / `text`) to handle malformed requests gracefully.
- **500 Recovery**: Global exception handlers catch system crashes and log the error without killing the server.
- **Graceful Failures**: If the Actor Agent fails to generate a reply, it falls back to a static "internet connection error" message to maintain the persona rather than crashing.
