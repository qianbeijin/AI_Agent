from fastapi import FastAPI
# 导入你的 chat 路由模块
from app.api.v1.endpoints import chat 
# 导入 CORS 中间件
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.models import chat as chat_model # 引入你刚才写的 chat.py 模型文件

app = FastAPI(title="AI Agent Backend")

# --- 关键步骤：自动建表 ---
# 这行代码会扫描所有继承自 Base 的模型，并在数据库中创建对应的表
Base.metadata.create_all(bind=engine)

# 允许跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何来源的前端访问（开发模式通用）
    allow_credentials=True,
    allow_methods=["*"],  # 允许 GET, POST, PUT 等所有方法
    allow_headers=["*"],  # 允许所有 Header\
)


# 注册路由
# prefix="/api/v1" 意味着这个文件里的所有接口地址都要加上这个前缀
# tags=["Chat"] 是为了在 Swagger 文档里分类好看
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.get("/")
def root():
    return {"message": "AI Backend is running!"}                                                                             