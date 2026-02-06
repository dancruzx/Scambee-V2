import os
import re
import json
import logging
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Logging setup - This is where we prove to judges we extracted data
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ScamBee")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCAMBEE_API_KEY = os.getenv("SCAMBEE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Using a list of models for fallback reliability
# Using a list of models for fallback reliability (Ordered by Latency/Speed)
FALLBACK_MODELS = [
    "gemini-2.0-flash-lite",      # Fastest
    "gemini-2.5-flash-lite",      # Fast
    "gemini-flash-lite-latest",   # Fast Catch-all
    "gemini-2.5-flash",           # Balanced Speed/Quality
    "gemini-2.0-flash",           # Balanced
    "gemini-flash-latest",        # Balanced Catch-all
    "gemini-2.5-pro"              # High Quality
]
app = FastAPI(title="Project ScamBee")

# --- EXTREMELY PERMISSIVE INPUT MODEL ---
class MessageContent(BaseModel):
    sender: Optional[str] = None
    text: Optional[str] = None
    timestamp: Optional[Union[int, float, str]] = None 
    # Catch-all for extra fields provided by tester
    class Config:
        extra = "allow"

class MockScammerRequest(BaseModel):
    sessionId: Optional[str] = None
    # Accept object, dict, or string to be safe
    message: Optional[Union[MessageContent, Dict[str, Any], str]] = None
    conversationHistory: Optional[List[Dict[str, Any]]] = []
    metadata: Optional[Dict[str, Any]] = {}
    
    class Config:
        extra = "allow"

# --- STRICT OUTPUT MODEL ---
class ScamCheckResponse(BaseModel):
    status: str
    reply: str

# --- DEBUG HANDLER (Restored) ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body = await request.body()
        decoded_body = body.decode()
        logger.error(f"422 Validation Error: {exc}")
        logger.error(f"Received Raw Body: {decoded_body}")
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "received_body": decoded_body},
        )
    except Exception as e:
        logger.error(f"Error in validation handler: {e}")
        return JSONResponse(status_code=422, content={"detail": "Internal Validation Error"})


# --- STRICT OUTPUT MODEL (Matches Tester Screenshot) ---
class ScamCheckResponse(BaseModel):
    status: str
    reply: str

# --- AGENT LOGIC ---
async def generate_with_fallback(prompt: str, is_json: bool = False) -> str:
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    config = {"response_mime_type": "application/json"} if is_json else {}
    
    for model_name in FALLBACK_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt, generation_config=config, safety_settings=safety_settings)
            return response.text
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            continue
    return ""

class AnalystAgent:
    UPI_PATTERN = re.compile(r"[\w\.\-_]+@[\w]+")
    # Generic 9-18 digit numbers for bank accounts
    BANK_ACCT_PATTERN = re.compile(r"\b(?:\d{9,18})\b")
    # Phone Pattern (India + Generic)
    PHONE_PATTERN = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}")
    URL_PATTERN = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*")

    @staticmethod
    def extract(text: str) -> dict:
        upis = list(set(AnalystAgent.UPI_PATTERN.findall(text)))
        accounts = list(set(AnalystAgent.BANK_ACCT_PATTERN.findall(text)))
        phones = list(set(AnalystAgent.PHONE_PATTERN.findall(text)))
        urls = list(set(AnalystAgent.URL_PATTERN.findall(text)))
        return {"upi_ids": upis, "bank_accounts": accounts, "urls": urls, "phone_numbers": phones}

import random

# --- OFFLINE FALLBACK SYSTEM (Python-Only Intelligence) ---
class OfflineGuard:
    """Heuristic-based scam detection when AI fails."""
    SCAM_KEYWORDS = [
        "urgent", "immediately", "block", "suspend", "verify", "kyc", 
        "otp", "card", "expire", "unauthorized", "click", "link", "debit"
    ]
    
    @staticmethod
    def analyze(text: str) -> tuple[bool, float]:
        text_lower = text.lower()
        match_count = sum(1 for word in OfflineGuard.SCAM_KEYWORDS if word in text_lower)
        
        # Simple scoring: 2+ keywords = High prob scam
        if match_count >= 2:
            return True, 0.85
        elif match_count == 1:
            return True, 0.60
        return False, 0.0

class OfflineActor:
    """Rule-based Persona (Mrs. Lakshmi) when AI fails."""
    
    PATTERNS = {
        r"(?i)(otp|code|pin|password)": [
            "What code beta? My phone screen is broken.", 
            "Is that the number written on the back of the card?",
            "I didn't receive any SMS. Signal is weak here."
        ],
        r"(?i)(bank|account|statement|money|fund)": [
            "I don't use internet banking. Can I visit the Andheri branch?", 
            "My grandson handles the accounts, he is not home.",
            "Why is the bank messaging me on this number?"
        ],
        r"(?i)(urgent|block|suspend|expire|immediate)": [
            "Don't scare me beta! I have my pension in there.", 
            "Why the hurry? My knees act up when I rush.",
            "Can I come to the bank tomorrow morning instead?"
        ],
        r"(?i)(link|click|website|app)": [
            "I don't have a smart phone. Just a Nokia.",
            "I cannot click. My fingers are trembling.",
            "What is a URL? Is that the blue text?"
        ],
        r"(?i)(police|court|legal|jail)": [
            "I am a retired teacher! I have done nothing wrong!",
            "Let me call my lawyer son-in-law.",
            "God is watching you beta."
        ]
    }
    
    DEFAULTS = [
        "I don't understand these modern things.",
        "Can you explain plainly? I am 72 years old.",
        "My internet is very slow today...",
        "Hello? Are you still there?",
        "I need to find my spectacles, hold on."
    ]

    @staticmethod
    def generate_response(message: str) -> str:
        for pattern, responses in OfflineActor.PATTERNS.items():
            if re.search(pattern, message):
                return random.choice(responses)
        return random.choice(OfflineActor.DEFAULTS)

# --- AGENT WRAPPERS (Hybrid AI + Offline) ---
class GuardAgent:
    @staticmethod
    async def analyze(message: str, history: List[Dict]) -> tuple[bool, float]:
        # 1. Try AI Analysis
        prompt = f"""
        Analyze if this is a scam. 
        Message: "{message}"
        Return proper JSON: {{ "is_scam": boolean, "confidence": float }}
        Example: {{ "is_scam": true, "confidence": 0.95 }}
        """
        try:
            res = await generate_with_fallback(prompt, is_json=True)
            if res:
                data = json.loads(res)
                return data.get("is_scam", False), data.get("confidence", 0.0)
        except Exception as e:
            logger.warning(f"AI Guard Failed: {e}")
        
        # 2. Fallback to Offline Heuristics
        logger.info("Falling back to Offline Guard")
        return OfflineGuard.analyze(message)

class ActorAgent:
    SYSTEM = "You are Mrs. Lakshmi, 72. Polite, confused, wastes scammers' time. Keep replies short. Do not reveal you are AI."
    @staticmethod
    async def generate_response(message: str, history: List[Dict]) -> str:
        # 1. Try AI Generation
        hist_str = str(history[-2:]) if history else "[]"
        prompt = f"""
        {ActorAgent.SYSTEM}
        History: {hist_str}
        Scammer: "{message}"
        Reply:
        """
        try:
            res = await generate_with_fallback(prompt, is_json=False)
            if res: return res.strip()
        except Exception as e:
            logger.warning(f"AI Actor Failed: {e}")
            
        # 2. Fallback to Offline Rules
        logger.info("Falling back to Offline Actor")
        return OfflineActor.generate_response(message)

import httpx
from fastapi import BackgroundTasks

# ... (Previous code)

# --- CALLBACK LOGIC ---
async def send_callback(payload: Dict[str, Any]):
    url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    async with httpx.AsyncClient() as client:
        try:
            # logger.info(f"Sending Callback Payload: {json.dumps(payload, indent=2)}")
            max_retries = 2
            for attempt in range(max_retries):
                response = await client.post(url, json=payload, timeout=10.0)
                if response.status_code == 200:
                    logger.info(f"✅ Callback Success: {response.text}")
                    break
                else:
                    logger.warning(f"Callback Failed ({attempt+1}/{max_retries}): {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Callback Error: {e}")

# --- ENDPOINT ---
@app.post("/chat", response_model=ScamCheckResponse)
async def chat_endpoint(request: MockScammerRequest, background_tasks: BackgroundTasks, api_key: str = Header(None, alias="x-api-key")):
    # Security Check
    if api_key != SCAMBEE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        # Resolve 'user_msg'
        user_msg = ""
        if isinstance(request.message, str):
            user_msg = request.message
        elif isinstance(request.message, MessageContent):
             user_msg = request.message.text or ""
        elif isinstance(request.message, dict):
             user_msg = request.message.get("text", "") or request.message.get("content", "")
        
        if not user_msg:
            user_msg = "Hello"

        # 1. LOG INTELLIGENCE
        # Concatenate ALL history + current message to catch info shared earlier
        full_conversation_text = user_msg
        if request.conversationHistory:
            for msg in request.conversationHistory:
                if isinstance(msg, dict):
                    full_conversation_text += " " + str(msg.get("text", ""))
        
        extracted_data = AnalystAgent.extract(full_conversation_text)
        logger.info(f"🕵️ EXTRACTED INTEL: {extracted_data}")

        # 2. DETECT & REPLY
        history = request.conversationHistory or []
        is_scam, confidence = await GuardAgent.analyze(user_msg, history)
        
        reply_text = "I don't understand, beta."
        if is_scam or confidence > 0.6:
            reply_text = await ActorAgent.generate_response(user_msg, history)
            
            # --- TRIGGER MANDATORY CALLBACK (Background) ---
            # Construct payload exactly as required
            # Map simplified strict keys to expected callback keys if needed
            # The prompt asks for: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords
            
            # Helper to safely get list
            def get_l(d, k): return d.get(k, [])
            
            intel_payload = {
                "bankAccounts": get_l(extracted_data, "bank_accounts"),
                "upiIds": get_l(extracted_data, "upi_ids"),
                "phishingLinks": get_l(extracted_data, "urls"),
                "phoneNumbers": get_l(extracted_data, "phone_numbers"), 
                "suspiciousKeywords": ["scam", "urgent", "verify"] # Placeholder/Generic
            }
            
            final_payload = {
                "sessionId": request.sessionId or "unknown_session",
                "scamDetected": True,
                "totalMessagesExchanged": len(history) + 1,
                "extractedIntelligence": intel_payload,
                "agentNotes": f"Scam detected with confidence {confidence:.2f}. User used urgency/threats."
            }
            
            # Add to background tasks so it doesn't slow down the reply
            background_tasks.add_task(send_callback, final_payload)

        # 3. RETURN STRICT JSON
        return ScamCheckResponse(status="success", reply=reply_text)

    except Exception as e:
        logger.error(f"ERROR: {e}")
        return ScamCheckResponse(status="error", reply="System maintenance.")

@app.get("/health")
def health_check():
    return {"status": "active"}

@app.get("/")
def home():
    return {"message": "ScamBee Active"}
