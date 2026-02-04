# 🐝 Project ScamBee

**An Agentic AI Honey-Pot System to Detect & Waste Scammers' Time.**

Project ScamBee is a high-performance FastAPI application designed to intercept scam messages. It uses Google Gemini 2.0 to detect scam intent and deploys a "Grandma Persona" (Mrs. Lakshmi) to engage the scammer, wasting their time while extracting intelligence (UPI IDs, URLs, Bank Accounts) in the background.

## 🚀 Live Demo
**API Endpoint:** `https://scambee-v2.onrender.com`
- **Docs:** [Swagger UI](https://scambee-v2.onrender.com/docs)
- **Method:** `POST /chat`

> **⚠️ Deployment Note:**
> This service is hosted on Render's **Free Tier**. The server goes to sleep after inactivity.
> **The first request may take 20-50 seconds to respond** while the instance spins up. 
> Subsequent requests will be instant (<1s).

## ✨ Features
- **🛡️ The Guard**: Analyzing messages for scam intent using **Gemini 2.0 / 2.5**.
- **🎭 The Actor**: "Mrs. Lakshmi", a confused elderly persona who wastes scammers' time.
- **🕵️ The Analyst**: Regex-based extraction of UPIs, Bank Accounts, and Phishing Links.
- **🔄 Model Fallback**: Automatically switches between `gemini-2.5-flash`, `2.0-flash`, and `pro` if one fails.
- **🔒 Security**: Protected via `x-api-key` header.

## 🛠️ API Usage

### Endpoint: `/chat`
**Headers:**
- `x-api-key`: `SuperSecretKeyForHCL2026`
- `Content-Type`: `application/json`

**Body:**
```json
{
  "session_id": "unique-id-123",
  "message": "Congratulations! You won a lottery. Pay $500 tax to claim.",
  "history": []
}
```

**Response:**
```json
{
  "is_scam": true,
  "confidence_score": 1.0,
  "generated_reply": "Oh my! A lottery? I verified nothing... how do I pay?",
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "urls": []
  },
  "engagement_metrics": {
    "mood": "Urgent",
    "turn_count": 1
  }
}
```

## 📦 Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/dancruzx/Scambee-V2.git
cd Scambee-V2
```

### 2. Environment Variables
Create a `.env` file:
```env
GEMINI_API_KEY=your_google_api_key
SCAMBEE_API_KEY=SuperSecretKeyForHCL2026
```

### 3. Run with Docker
```bash
docker build -t scambee .
docker run -p 8000:8000 scambee
```

### 4. Run Locally (Python)
```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```
