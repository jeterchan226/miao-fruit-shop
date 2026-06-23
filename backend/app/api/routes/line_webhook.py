import asyncio

from fastapi import APIRouter, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.services import line_service

router = APIRouter(prefix="/api", tags=["line"])


@router.post("/line/webhook")
async def line_webhook(request: Request) -> dict[str, str]:
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")
    try:
        await asyncio.to_thread(line_service.handle_webhook_events, body, signature)
    except InvalidSignatureError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc
    return {"status": "ok"}
