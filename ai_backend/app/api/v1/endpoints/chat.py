from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse  # 👈 核心组件
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.chat import ChatRequest
from app.services.memory import MemoryService

router = APIRouter()

@router.post("/chat") # 注意：这里去掉了 response_model=ChatResponse，因为返回的是流
async def chat_endpoint(
    request: ChatRequest, 
    db: Session = Depends(get_db)
):
    # 1. 确定 Session ID
    session_id = request.session_id
    if not session_id:
        session_id = MemoryService.create_session()

    # 2. 准备上下文 (System + History)
    history = MemoryService.get_history(db, session_id)
    system_prompt = {"role": "system", "content": "你是一个乐于助人的 AI 编程助手。"}
    current_message = {"role": "user", "content": request.message}
    
    full_context = [system_prompt] + history + [current_message]

    # 3. 【关键变化】先存用户的消息
    # 在流开始之前，先把用户说的话落库，确保数据安全
    MemoryService.add_message(db, session_id, "user", request.message)

    # 4. 直接把 Service 层的生成器扔给 Response
    # 去掉了中间冗余的 async def generate()
    return StreamingResponse(
        MemoryService.stream_and_save_wrapper(db, session_id, full_context),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id}
    )