from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse  # 👈 核心组件
# 用于传统的同步（阻塞式）数据库操作
# from sqlalchemy.orm import Session
# 用于异步（非阻塞）数据库操作
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.chat import ChatRequest
from app.services.memory import MemoryService
from app.services.retrieval import get_relevant_context

from app.services.llm import get_deepseek_response

router = APIRouter()

@router.post("/chat") # 注意：这里去掉了 response_model=ChatResponse，因为返回的是流
async def chat_endpoint(
    request: ChatRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    RAG 流式对话核心接口
    """

    # 1. 确定 Session ID
    session_id = request.session_id
    if not session_id:
        session_id = MemoryService.create_session()

    # 1.根据用户的问题进行向量化检索
    context = await get_relevant_context(db=db, question=request.message, top_k=3)
    print(context)

    # 2.Prompt组装
    # 核心防御：必须在系统提示词中圈定模型的知识边界，防止AI乱回答
    prompt = f"""
    你是一个企业级智能助理。请严格根据以下【背景知识】回答用户问题。
    如果背景知识中没有相关信息，请直接回答“知识库中暂无相关信息，我无法准确回答”，绝不允许编造。

    【背景知识】:
    {context}
    """

    # # 2. 准备上下文 (System + History)
    # history = MemoryService.get_history(db, session_id)
    system_prompt = {"role": "system", "content": prompt}
    current_message = {"role": "user", "content": request.message}
    
    full_context = [system_prompt] + [current_message]

    # # 3. 【关键变化】先存用户的消息
    # # 在流开始之前，先把用户说的话落库，确保数据安全
    # MemoryService.add_message(db, session_id, "user", request.message)
    
    # 4. 直接把 Service 层的生成器扔给 Response
    # 去掉了中间冗余的 async def generate()
    return StreamingResponse(
        get_deepseek_response(full_context),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id}
    )