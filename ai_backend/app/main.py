from fastapi import FastAPI
# 导入你的 chat 路由模块
from app.api.v1.endpoints import chat 

app = FastAPI(title="AI Agent Backend")

# 注册路由
# prefix="/api/v1" 意味着这个文件里的所有接口地址都要加上这个前缀
# tags=["Chat"] 是为了在 Swagger 文档里分类好看
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.get("/")
def root():
    return {"message": "AI Backend is running!"}