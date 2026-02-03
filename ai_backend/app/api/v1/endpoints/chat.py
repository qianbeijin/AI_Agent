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

    # 4. 定义流式生成器 (闭包函数)
    # 我们在这里调用 Service 层的 wrapper，把 db 传进去
    async def generate():
        # 调用 Service 层写好的“边吐字边存库”的方法
        # 注意：你需要确保 memory.py 里有 stream_and_save_wrapper 这个方法
        async for chunk in MemoryService.stream_and_save_wrapper(db, session_id, full_context):
            yield chunk

    # 5. 返回流式响应
    return StreamingResponse(
        generate(),
        media_type="text/event-stream", # 👈 告诉浏览器：这是流，别关连接
        headers={
            "X-Session-Id": session_id  # 👈 技巧：把 Session ID 藏在响应头里传回去
        }
    )