import os
import httpx
from sqlalchemy.orm import Session
from app.models.document import DocumentChunk  # 确保路径正确
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
# 硅基流动的标准 OpenAI 兼容接口地址
EMBEDDING_BASE_URL = "https://api.siliconflow.cn/v1/embeddings"

async def get_embedding(text: str) -> list:
    """
    调用外包引擎（硅基流动）将文本转为向量
    """
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "BAAI/bge-m3", # 业界最强开源中文向量模型
        "input": text,
        "encoding_format": "float"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(EMBEDDING_BASE_URL, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            result = response.json()
            # 提取向量数组 [0.12, -0.05, ...]
            return result["data"][0]["embedding"]
        except Exception as e:
            print(f"❌ 获取向量失败: {e}")
            return None

async def process_and_store_document(db: Session, content: str, source: str):
    """
    简单的切片并存储逻辑（MVP版本）
    """
    # 1. 简单切片：这里先演示按 500 字强制切分
    # 以后我们会升级为更高级的“语义重叠切片”
    chunks = [content[i:i+500] for i in range(0, len(content), 500)]
    
    print(f"📦 开始处理文档：{source}，共切分为 {len(chunks)} 个片段")
    
    for i, chunk_text in enumerate(chunks):
        # 2. 获取向量
        vector = await get_embedding(chunk_text)
        
        if vector:
            # 3. 构造数据库模型
            new_chunk = DocumentChunk(
                content=chunk_text,
                embedding=vector,
                source_file=source
            )
            # 4. 写入 PostgreSQL
            db.add(new_chunk)
            print(f"✅ 已存入第 {i+1}/{len(chunks)} 个片段")
    
    db.commit()
    print("🚀 所有片段已成功注入向量数据库！")