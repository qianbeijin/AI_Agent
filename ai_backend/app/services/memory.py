from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # 🌟 异步改造：引入 AsyncSession
from sqlalchemy import select                    # 🌟 异步改造：引入 select 构造器
from app.models.chat import ChatMessage
import uuid
from app.services.llm import get_deepseek_response

# 限制上下文长度（防止 Token 爆炸）
MAX_HISTORY_LEN = 20 

class MemoryService:
    @staticmethod
    async def get_history(db: AsyncSession, session_id: str): # <--- 注意这里多了一个 db 参数
        """
        纯粹的业务逻辑：查询历史记录(异步查询)
        """

        # 直接使用传入的 db 进行查询
        # 🌟 异步改造：2.0 风格的 select 语句
        stmt = select(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.id.asc())

        # 🌟 异步改造：执行查询并获取结果
        result = await db.execute(stmt)
        messages = result.scalars().all()

        # 转为字典返回给 API
        return [{"role": m.role, "content": m.content} for m in messages]

    @staticmethod
    async def add_message(db: AsyncSession, session_id: str, role: str, content: str):
        """
        异步存入消息 (带工业级事务防御)
        """
        try:
            new_msg = ChatMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(new_msg)
            await db.commit()   
            await db.refresh(new_msg) 
            
        except SQLAlchemyError as e:
            # 🌟 致命防御 1：立刻回滚，把脏数据从内存踢出去，保住整个连接池！
            await db.rollback() 
            
            # 🌟 致命防御 2：这里千万不要用 raise 把异常抛出去！
            # 因为给用户的字已经流式输出完了，你抛出异常会导致流的最后报个 500 错误，前端会断开。
            # 正确的做法是：记录一条严重的后端日志，让运维明天来修，但不能影响当前用户的体验。
            print(f"🚨 [严重警告] 聊天记录落盘失败! Session: {session_id} | 错误: {str(e)}")
            # logging.error(f"DB Write Failed: {e}")

    @staticmethod
    def create_session() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    async def stream_and_save_wrapper(db: AsyncSession, session_id: str, messages: list):
        """
        包装器生成器：
        1. 转发 LLM 的流给前端
        2. 收集完整回复并存入数据库
        """
        full_response = ""
        
        # 调用上面写的 LLM 流
        async for chunk in get_deepseek_response(messages):
            full_response += chunk  # 偷偷拼接
            yield chunk             # 继续往前端吐字

        # --- 当流结束（循环退出）后，执行存库操作 ---
        # 注意：这里调用我们昨天写的 add_message
        await MemoryService.add_message(db, session_id, "assistant", full_response)