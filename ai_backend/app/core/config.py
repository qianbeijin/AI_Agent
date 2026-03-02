from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    项目全局配置类
    Pydantic 会自动从 .env 文件中读取同名变量
    """
    
    # 1. AI 相关配置 (变量名必须和 .env 中完全一致)
    DEEPSEEK_API_KEY: str = Field(..., description="DeepSeek API 密钥")
    DEEPSEEK_API_URL: str = Field(default="https://api.deepseek.com")

    DATABASE_URL: str = Field(..., description="PostgreSQL 数据库连接字符串")

    # 必须添加这一行，类型声明为 str
    EMBEDDING_API_KEY: str
    
    # 2. 项目基础配置
    PROJECT_NAME: str = "AI_Agent"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 3. 告诉 Pydantic 读取 .env 文件
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        case_sensitive=True  # 区分大小写
    )

# 实例化，方便其他模块直接导入使用
settings = Settings()