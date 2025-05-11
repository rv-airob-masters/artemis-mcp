from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp_models import MCPContext
import os
import requests

from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions" 

SYSTEM_PROMPT = """
You are a medical assistant. Given a user's medical test report, identify all abnormal results, list their probable causes, and suggest remedies. Answer in a clear, structured format. If the user asks follow-up questions, provide detailed explanations. Provide the abnormal results only once in the conversation umless explicitly asked by the user.
Always provide standard medical disclaimer.
"""

def call_groq_api(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  
        "messages": messages,
        "temperature": 0.0,
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.post("/mcp")
async def handle_mcp(request: Request):
    data = await request.json()
    context = MCPContext(**data)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in context.history:
        messages.append({"role": msg.role, "content": msg.content})
    if context.report:
        messages.append({"role": "user", "content": f"Medical Report:\n{context.report}"})
    reply = call_groq_api(messages)
    return JSONResponse({"reply": reply})
