from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class ChatMessage(Base):
    # 表名
    __tablename__ = "chat_messages"

    # 字段定义
    # primary_key=True: 主键，每条数据唯一的身份证号
    # index=True: 加索引，为了查询更快
    id = Column(Integer, primary_key=True, index=True)
    
    # session_id: 必须要加索引，因为我们总是通过 session_id 来查聊天记录
    session_id = Column(String(50), index=True, nullable=False)
    
    # role: 'user' 或 'assistant'，长度不长，用 String
    role = Column(String(20), nullable=False)
    
    # content: 内容可能很长，必须用 Text 类型
    content = Column(Text, nullable=False)
    
    # created_at: 自动记录创建时间，非常重要
    created_at = Column(DateTime(timezone=True), server_default=func.now())