from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# 定义单条消息的结构（符合 OpenAI/DeepSeek 格式规范）
class message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

# 接收前端的数据格式
class ChatRequest(BaseModel):
    # session_id 可选。如果是第一次对话，前端可能不传，由后端生成返回
    session_id: Optional[str] = Field(default=None, description="会话唯一标识")
    message: str = Field(..., min_length=1, description="用户发送的内容")

# 返回给前端的数据格式
class ChatResponse(BaseModel):
    session_id: str
    answer: str

