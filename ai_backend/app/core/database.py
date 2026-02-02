from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 数据库地址
# 这里的 sqlite:///./chat.db 表示在当前目录下生成一个 chat.db 文件
# 未来如果想换 MySQL，只需要把这行改成: "mysql+pymysql://user:pass@localhost/dbname"
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat.db"

# 2. 创建引擎
# connect_args={"check_same_thread": False} 是 SQLite 特有的配置，换 MySQL 时要去掉
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 基础模型类
Base = declarative_base()

# 5. 依赖注入工具 (用于在 API 中获取数据库连接)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()