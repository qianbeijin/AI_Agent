from fastapi import FastAPI
# 导入你的 chat 路由模块
from app.api.v1.endpoints import chat 
# 导入 CORS 中间件
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, Base, get_db
# 确保导入了刚才写的 Model，否则 SQLAlchemy 扫描不到它
from app.models.document import DocumentChunk   # noqa: F401
from sqlalchemy import text

from app.services.ingestion import process_and_store_document
from fastapi import Depends
from sqlalchemy.orm import Session



# 注册路由
# prefix="/api/v1" 意味着这个文件里的所有接口地址都要加上这个前缀
# tags=["Chat"] 是为了在 Swagger 文档里分类好看

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================================
    # 服务启动时执行：数据库初始化与向量插件激活
    # ==========================================
    print("🚀 正在初始化数据库底层基础设施...")
    with engine.connect() as conn:
        # 1. 强制激活 extra="forbid" 的 vector 扩展（极其重要）
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # 2. 根据 Model 自动在库中建立对应的表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表同步完成，pgvector 引擎已激活！")
    
    yield # 这里是交接控制权给 FastAPI，服务正式运行
    
    # ==========================================
    # 服务关闭时执行：资源清理
    # ==========================================
    print("🛑 服务正在关闭...")

# 初始化 FastAPI 实例，注入生命周期
app = FastAPI(
    title="AI Agent Backend",
    lifespan=lifespan
)

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

# 允许跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何来源的前端访问（开发模式通用）
    allow_credentials=True,
    allow_methods=["*"],  # 允许 GET, POST, PUT 等所有方法
    allow_headers=["*"],  # 允许所有 Header\
    # --- 核心修改点 ---
    # 必须显式列出允许前端 JS 读取的自定义 Header
    expose_headers=["X-Session-Id"] 
)


@app.get("/")
def root():
    return {"message": "AI Backend is running!"}      
