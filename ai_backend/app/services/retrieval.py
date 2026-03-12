from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import DocumentChunk
from app.services.embedding import get_embedding
import uuid

# top_k限定只要相似度最高的前三条
async def get_relevant_context(db: AsyncSession, question: str, top_k: int = 3, doc_id: str = None) :
    """
    RAG 核心检索函数：将问题转为向量，并去数据库捞取最相似的片段
    """
    # 1. 翻译用户问题，加上字数防御限制
    if len(question) > 2000:
        question = question[:2000] # 直接截断，简单粗暴

    question_vector = await get_embedding(question)

    if not question_vector:
        return "⚠️ 抱歉，提取问题特征时发生网络异常，请重试。"

    # 2. 拿着翻译好的坐标 (query_vector) 去查字典
    try: 

        # db: Session 是 SQLAlchemy 的同步 Session， 在 async def 函数中直接调用它，会阻塞整个 asyncio 事件循环，失去异步优势
        # 异步查询必须用 await + execute()
        # results = db.query(DocumentChunk).order_by(
        #     DocumentChunk.vector.op('<->')(question_vector)
        # ).limit(top_k).all()

        # 构造异步查询
        stmt = select(DocumentChunk)
        if(doc_id) :
            # 如果前端传了 doc_id，就只在这篇文档里搜
            # 不管前端传来的是什么妖魔鬼怪，强行转成纯字符串，并去掉首尾空格
            clean_doc_id = str(doc_id).strip()
            stmt = stmt.filter(DocumentChunk.doc_id == clean_doc_id)
        stmt = stmt.order_by(
            DocumentChunk.vector.op('<->')(question_vector)
        ).limit(top_k)

        result = await db.execute(stmt)  # 👈 必须 await
        results = result.scalars().all()  # 提取对象列表


        # 3. 结果判断
        if not results:
            return "知识库中暂无相关上下文信息。"
        
        # 4. 上下文重组
        context = "\n\n---\n\n".join([r.content for r in results])

        return context
    except Exception as e:
        await db.rollback()
        print(f"❌ 数据库检索失败: {e}")
        return "⚠️ 知识库检索时发生系统错误。"

    