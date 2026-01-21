from fastapi import APIRouter, HTTPException
from app.services.llm import get_deepseek_response
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.message
    ai_reply = await get_deepseek_response(user_input)
    return ChatResponse(answer=ai_reply)