import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 强制加载项目根目录的 .env 文件
load_dotenv()

# 2. 从环境变量中安全获取数据库 URL
# 如果 .env 没配好，这里会报错，这叫“快速失败 (Fail-Fast)”机制，是好事情
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("数据库地址未配置！请检查 .env 文件中的 DATABASE_URL")

# 3. 创建引擎 
# ⚠️ 注意：这里已经去掉了 SQLite 特有的 connect_args={"check_same_thread": False}
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 4. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. 基础模型类
Base = declarative_base()

# 下面的 get_db() 函数保持你截图里的原样即可
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()