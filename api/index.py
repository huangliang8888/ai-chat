"""
AI Chat API - Main entry point for Vercel serverless function
"""
import os
import json
import logging
from typing import Optional

# Load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chat API", version="1.0.0")

# CORS - allow all origins for development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurable model via environment variable
AI_MODEL = os.environ.get("AI_MODEL", "qwen/qwen3-coder:free")


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    messages: list[ChatMessage] = Field(min_length=1)
    stream: Optional[bool] = True


# ---------- Supabase helpers ----------

def get_supabase():
    """Get Supabase client, returns None if not configured."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"Failed to get Supabase client: {e}")
        return None


async def save_message(session_id: str, role: str, content: str):
    """Save a message to Supabase."""
    sb = get_supabase()
    if not sb:
        return
    try:
        sb.table("chat_messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content,
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to save message: {e}")


async def get_history(session_id: str, limit: int = 50) -> list[dict]:
    """Get chat history from Supabase."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        result = sb.table("chat_messages") \
            .select("role, content") \
            .eq("session_id", session_id) \
            .order("created_at") \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"Failed to get history: {e}")
        return []


# ---------- OpenRouter API ----------

async def call_openrouter_stream(messages: list[dict]):
    """Call OpenRouter API with streaming."""
    import httpx

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    site_url = os.environ.get("SITE_URL", "http://localhost:5173")
    site_name = os.environ.get("SITE_NAME", "AI Chat")

    async def event_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": site_url,
                    "X-OpenRouter-Title": site_name,
                },
                json={
                    "model": AI_MODEL,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_msg = json.dumps({"content": f"AI 服务错误: {response.status_code}"})
                    yield f"data: {error_msg}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                out = json.dumps({"content": content}, ensure_ascii=False)
                                yield f"data: {out}\n\n"
                        except (json.JSONDecodeError, IndexError, KeyError):
                            continue

                yield "data: [DONE]\n\n"

    return event_generator()


async def call_openrouter_sync(messages: list[dict]) -> str:
    """Call OpenRouter API without streaming."""
    import httpx

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    site_url = os.environ.get("SITE_URL", "http://localhost:5173")
    site_name = os.environ.get("SITE_NAME", "AI Chat")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": site_url,
                "X-OpenRouter-Title": site_name,
            },
            json={
                "model": AI_MODEL,
                "messages": messages,
                "stream": False,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"AI service error: {response.status_code}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]


# ---------- Routes ----------

@app.get("/api")
async def root():
    return {"status": "ok", "message": "AI Chat API is running"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    # Build messages for OpenRouter
    system_msg = {
        "role": "system",
        "content": "你是一个友好、专业的 AI 助手。请用中文回答用户的问题。如果你的回答中包含代码，请使用 markdown 代码块格式。"
    }
    api_messages = [system_msg] + [{"role": m.role, "content": m.content} for m in req.messages]

    # Save user message to Supabase
    if req.messages:
        last_user_msg = req.messages[-1]
        if last_user_msg.role == "user":
            await save_message(req.session_id, "user", last_user_msg.content)

    if req.stream:
        # Streaming response
        generator = await call_openrouter_stream(api_messages)

        # We need to also save the assistant response - but with streaming
        # we'll collect it in a wrapper
        collected_content = []

        async def saving_generator():
            async for chunk in generator:
                collected_content.append(chunk)
                yield chunk
            # After streaming is done, save the full response
            full_text = ""
            for c in collected_content:
                if c.startswith("data: ") and "[DONE]" not in c:
                    try:
                        parsed = json.loads(c[6:].strip())
                        full_text += parsed.get("content", "")
                    except (json.JSONDecodeError, AttributeError):
                        pass
            if full_text:
                await save_message(req.session_id, "assistant", full_text)

        return StreamingResponse(
            saving_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming response
        content = await call_openrouter_sync(api_messages)
        await save_message(req.session_id, "assistant", content)
        return {"content": content, "role": "assistant"}


@app.get("/api/history/{session_id}")
async def history(session_id: str):
    messages = await get_history(session_id)
    return {"messages": messages}
