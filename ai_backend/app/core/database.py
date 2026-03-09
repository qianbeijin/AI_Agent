import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# 1. 强制加载项目根目录的 .env 文件
load_dotenv()

# 2. 从环境变量中安全获取数据库 URL
raw_url = os.getenv("DATABASE_URL")
if not raw_url:
    raise ValueError("数据库地址未配置！请检查 .env 文件中的 DATABASE_URL")

# 【核心防御机制】：确保使用的是异步驱动 asyncpg
# 如果你的 .env 里写的是 postgresql://，这里会自动为你替换为 postgresql+asyncpg://
if raw_url.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    SQLALCHEMY_DATABASE_URL = raw_url

# 3. 创建异步引擎 (非阻塞I/O核心)
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # 生产环境建议保持 False，避免终端被 SQL 日志淹没
    pool_pre_ping=True # 每次从连接池获取连接前，验证连接是否存活
)

# 4. 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False  # 【极度重要】：防止在异步流式输出期间访问模型属性时触发 DetachedInstanceError
)

# 5. 基础模型类
Base = declarative_base()

# 6. 异步依赖注入函数 (供 FastAPI 路由使用)
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        # 无论成功或异常，强制释放连接回连接池
        await db.close()