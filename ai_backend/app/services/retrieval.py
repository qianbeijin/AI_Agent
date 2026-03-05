from sqlalchemy.orm import Session
from models.document import DocumentChunk
from app.services.embedding import get_embedding

# top_k限定只要相似度最高的前三条
async def get_relevant_context(db: Session, question: str, top_k: int = 3) :
    """
    RAG 核心检索函数：将问题转为向量，并去数据库捞取最相似的片段
    """
    # 1. 翻译用户问题，加上字数防御限制
    if len(question) > 2000:
        question = question[:2000] # 直接截断，简单粗暴

    question_vector = await get_embedding(question)