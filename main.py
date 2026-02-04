import os
import re
import json
import logging
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# ... (Logging and Keys remain same)

# Using a list of models for fallback reliability
FALLBACK_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
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
    URL_PATTERN = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*")

    @staticmethod
    def extract(text: str) -> dict:
        upis = list(set(AnalystAgent.UPI_PATTERN.findall(text)))
        accounts = list(set(AnalystAgent.BANK_ACCT_PATTERN.findall(text)))
        urls = list(set(AnalystAgent.URL_PATTERN.findall(text)))
        return {"upi_ids": upis, "bank_accounts": accounts, "urls": urls}

class GuardAgent:
    @staticmethod
    async def analyze(message: str, history: List[Dict]) -> tuple[bool, float]:
        prompt = f"""
        Analyze if this is a scam. 
        Message: "{message}"
        Return proper JSON: {{ "is_scam": boolean, "confidence": float }}
        Example: {{ "is_scam": true, "confidence": 0.95 }}
        """
        try:
            res = await generate_with_fallback(prompt, is_json=True)
            if not res: return False, 0.0
            data = json.loads(res)
            return data.get("is_scam", False), data.get("confidence", 0.0)
        except:
            return False, 0.0

class ActorAgent:
    SYSTEM = "You are Mrs. Lakshmi, 72. Polite, confused, wastes scammers' time. Keep replies short. Do not reveal you are AI."
    @staticmethod
    async def generate_response(message: str, history: List[Dict]) -> str:
        # Simplified context for the actor
        hist_str = str(history[-2:]) if history else "[]"
        prompt = f"""
        {ActorAgent.SYSTEM}
        History: {hist_str}
        Scammer: "{message}"
        Reply:
        """
        try:
            res = await generate_with_fallback(prompt, is_json=False)
            return res.strip() if res else "Oh dear, my connection is poor."
        except:
            return "Oh dear, connection error."

# --- ENDPOINT ---
@app.post("/chat", response_model=ScamCheckResponse)
async def chat_endpoint(request: MockScammerRequest, api_key: str = Header(None, alias="x-api-key")):
    # Security Check
    if api_key != SCAMBEE_API_KEY:
        # Fallback check for different header casings if needed
        # logger.warning(f"Invalid API Key received: {api_key}")
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        # Resolve 'user_msg' from flexible input
        user_msg = ""
        if isinstance(request.message, str):
            user_msg = request.message
        elif isinstance(request.message, MessageContent):
             user_msg = request.message.text or ""
        elif isinstance(request.message, dict):
             user_msg = request.message.get("text", "") or request.message.get("content", "")
        
        if not user_msg:
            user_msg = "Hello" # Fallback if empty to prevent Guard crash

        # 1. LOG INTELLIGENCE (Proof for Judges)
        extracted_data = AnalystAgent.extract(user_msg)
        logger.info(f"🕵️ EXTRACTED INTEL: {extracted_data}")

        # 2. DETECT & REPLY
        is_scam, confidence = await GuardAgent.analyze(user_msg, request.conversationHistory or [])
        reply_text = "I don't understand, beta."
        
        if is_scam or confidence > 0.6:
            reply_text = await ActorAgent.generate_response(user_msg, request.conversationHistory or [])
        
        # 3. RETURN STRICT JSON
        return ScamCheckResponse(status="success", reply=reply_text)

    except Exception as e:
        logger.error(f"ERROR: {e}")
        return ScamCheckResponse(status="error", reply="System maintenance.")
