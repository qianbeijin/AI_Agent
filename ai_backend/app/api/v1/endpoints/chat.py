from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db          # 1. 引入拿连接的工具
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import get_deepseek_response
from app.services.memory import MemoryService # 2. 引入 Service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    db: Session = Depends(get_db) # 3. 依赖注入：FastAPI 自动帮你拿一个数据库连接
):
    # --- 1. 处理 Session ID ---
    session_id = request.session_id
    if not session_id:
        session_id = MemoryService.create_session()

    # --- 2. 调用 Service 获取历史 ---
    # 关键点：把 db 传给 Service
    history = MemoryService.get_history(db, session_id) 

    # --- 3. 组装 LLM 请求 ---
    current_message = {"role": "user", "content": request.message}
    system_prompt = {"role": "system", "content": "你是一个乐于助人的 AI 编程助手。"}
    full_context = [system_prompt] + history + [current_message]

    # --- 4. 调用 AI ---
    ai_content = await get_deepseek_response(full_context)

    # --- 5. 调用 Service 存入数据库 ---
    # 关键点：再次把 db 传给 Service，让它去存
    MemoryService.add_message(db, session_id, "user", request.message)
    MemoryService.add_message(db, session_id, "ai", ai_content)

    return ChatResponse(
        session_id=session_id,
        answer=ai_content
    )