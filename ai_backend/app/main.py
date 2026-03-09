from fastapi import FastAPI
# 导入你的 chat 路由模块
from app.api.v1.endpoints import chat, file

# 导入 CORS 中间件
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from sqlalchemy import text

# 【核心修复】：必须显式导入模型，否则 Base.metadata.create_all 不会建表！
from app.models.document import DocumentChunk



# 注册路由
# prefix="/api/v1" 意味着这个文件里的所有接口地址都要加上这个前缀
# tags=["Chat"] 是为了在 Swagger 文档里分类好看

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================================
    # 服务启动时执行：数据库初始化与向量插件激活
    # ==========================================
    print("🚀 正在初始化数据库底层基础设施...")
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        # Step 1: 强行激活 pgvector 插件 (必须在最前面)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Step 2: 插件激活后，Postgres 认识 vector 类型了，再执行建表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表同步完成，pgvector 引擎已激活！")

    
    yield # 这里是交接控制权给 FastAPI，服务正式运行
    
    # ==========================================
    # 服务关闭时执行：资源清理
    # ==========================================
    print("🛑 服务正在关闭...")
    # 显式关闭并清理引擎持有的所有数据库连接资源
    await engine.dispose()

# 初始化 FastAPI 实例，注入生命周期
app = FastAPI(
    title="AI Agent Backend",
    lifespan=lifespan
)

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(file.router, prefix="/api/v1", tags=["Files"])

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
