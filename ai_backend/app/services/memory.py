from sqlalchemy.orm import Session
from app.models.chat import ChatMessage
import uuid

# 限制上下文长度（防止 Token 爆炸）
MAX_HISTORY_LEN = 20 

class MemoryService:
    @staticmethod
    def get_history(db: Session, session_id: str): # <--- 注意这里多了一个 db 参数
        """
        纯粹的业务逻辑：查询历史记录
        """
        # 直接使用传入的 db 进行查询
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.id.asc())\
            .all()
        
        # 转为字典返回给 API
        return [{"role": m.role, "content": m.content} for m in messages]

    @staticmethod
    def add_message(db: Session, session_id: str, role: str, content: str): # <--- 这里也接收 db
        """
        纯粹的业务逻辑：存入消息
        """
        new_msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(new_msg)
        db.commit()   # 提交事务
        db.refresh(new_msg)

    @staticmethod
    def create_session() -> str:
        return str(uuid.uuid4())