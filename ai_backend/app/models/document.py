from sqlalchemy import JSON, Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
# 👈 核心引入：pgvector 提供的 SQLAlchemy 数据类型
from pgvector.sqlalchemy import Vector 
from app.core.database import Base

class DocumentChunk(Base):
    """
    RAG 系统的核心表：文档切片与向量存储表
    """
    __tablename__ = "document_chunks"

    doc_id = Column(Integer, primary_key=True, index=True)
    # 原始文本内容（比如：切分出来的一段法律条文）
    content = Column(Text, nullable=False)
    
    # 👈 决定薪资的核心字段：向量维度
    # 1024 是 硅基流动的标准维度
    # 这意味着一段文本会被转换成 1024 个浮点数
    vector = Column(Vector(1024)) 
    
    # 文件的来源（比如：劳动法.pdf，方便后续过滤）
    source_file = Column(String(255), index=True)
    # 🌟 新增：存放 metadata 的 JSON 字段，用来存 chunk_index 等结构化数据
    metadata_ = Column("metadata", JSON, nullable=True) # 注意：为了避免 Python 内部冲突，有时会做个别名映射，但直接用 metadata = Column(JSON) 通常也没问题
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())