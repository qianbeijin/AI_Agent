from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # 导入数据库专门的异常
from app.models.document import DocumentChunk  # 确保路径正确
from app.services.embedding import get_embedding  # 将翻译方法导入
import re  # 导入正则
import uuid # 引入 UUID 库生成唯一标识

async def process_and_store_document(db: Session, content: str, source: str, overlap: int, chunk_size: int) -> int:

    # 生成文档级唯一的uuid
    document_id = str(uuid.uuid4())
    
    # 1. 数据清洗
    # 将文本中的连续换行符替换为单换行，去除两端空格
    cleaned_content = re.sub(r'\n{2,}', '\n', content).strip()

    # 2. 滑动窗口切片
    # 设定参数：分块大小, 重叠度
    if chunk_size <= overlap:
        raise ValueError("chunk_size 必须大于 overlap")
    chunks = [
        cleaned_content[i:i+chunk_size]
        for i in range(0, len(cleaned_content), chunk_size - overlap)
        if cleaned_content[i:i+chunk_size]  # 过滤掉空字符串
    ]
    print(f"📦 开始处理文档：{source}，共切分为 {len(chunks)} 个片段")
    
    # 3. 批量向量化与存储 (加入极致的防御性事务控制)
    # 这是典型的 ETL 流程：抽取(Extract) -> 转换(Transform) -> 加载(Load)
    # 循环遍历 所有分块列表 (带上 索引i):
    successful_chunks = 0
    try:
        for i, chunk_text in enumerate(chunks):
            try:
                # 提示：工业级代码这里会封装 retry 机制
                vector = await get_embedding(chunk_text)
                
                if vector:
                    new_chunk = DocumentChunk(
                        doc_id=document_id, # 使用 UUID
                        content=chunk_text,
                        vector=vector,
                        source_file=source,
                        metadata={"chunk_index": i, "total_chunks": len(chunks)}
                    )
                    db.add(new_chunk)
                    successful_chunks += 1
                    
            except Exception as api_err:
                # 某一个片段 API 调用失败，记录日志，但【跳过】，不要卡死整个文档
                print(f"⚠️ 第 {i} 个片段向量化失败，跳过: {api_err}")
                continue 

        # 4. 提交事务 (只有在循环全结束，且没有发生致命异常时才提交)
        db.commit()
        print(f"🚀 文档 {source} 注入完毕！成功: {successful_chunks}/{len(chunks)}")
        return successful_chunks

    except SQLAlchemyError as db_err:
        # 规范 3：发生数据库级别错误，必须立刻回滚！
        db.rollback()
        print(f"❌ 数据库写入发生致命错误，已回滚: {db_err}")
        raise # 把异常抛给更上层（如路由组件）去给前端返回 500 错误