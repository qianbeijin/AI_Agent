from pydantic import BaseModel,Field

# 接收前端的数据格式
class ChatRequest(BaseModel):
    message: str

# 返回给前端的数据格式
class ChatResponse(BaseModel):
    answer: str

