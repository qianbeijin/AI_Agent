import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, HTTPException, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.services.ingestion import process_and_store_document
from app.models.document import DocumentChunk

import fitz  # 引入 PyMuPDF
import io
import re

router = APIRouter()

# 上传文件
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    RAG 离线数据灌装接口
    """
    # 1. 基础校验 (防御性编程)
    if not file.filename.endswith((".txt", ".md", ".pdf")):
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 2. 生成全局唯一文档 ID 
    document_id = str(uuid.uuid4())

    # 3. 构造元数据(可有可无)
    meta_data = {
        "file_size": file.size,
        "content_type": file.content_type
    }

    # 读取文件的二进制流
    content_bytes = await file.read()

    # 提取文件后缀名，转化为小写
    file_extension = file.filename.split('.')[-1].lower()
    extracted_text = ""

    try:
        # 根据不同文件名进行不同操作
        if file_extension == 'txt':
            extracted_text = content_bytes.decode('utf-8')
        elif file_extension == 'pdf':
            pdf_stream = io.BytesIO(content_bytes)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            
            clean_text_blocks = []
            
            for page in doc:
                # 获取当前页的原始文本
                page_text = page.get_text()
                
                # 将文本按行打散
                lines = page_text.split('\n')
                
                valid_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    
                    # 🛡️ 过滤规则 1：跳过空行
                    if not line_stripped:
                        continue
                        
                    # 🛡️ 过滤规则 2：无情击杀“纯数字行”（99%是页码）
                    if line_stripped.isdigit():
                        continue
                        
                    # 🛡️ 过滤规则 3：击杀常见的带有修饰的页码（比如 "- 14 -" 或 "Page 14"）
                    # 使用正则匹配：开头结尾可能有横线、空格，中间是数字
                    if re.match(r'^[-—\s]*(page)?\s*\d+\s*[-—\s]*$', line_stripped, re.IGNORECASE):
                        continue
                        
                    # 如果这行数据是清白的，加入有效行
                    valid_lines.append(line_stripped)
                    
                # 把清洗后的这一页行重新拼起来（用空格代替原来的回车，防止句子被粗暴切断）
                page_clean_text = " ".join(valid_lines)
                clean_text_blocks.append(page_clean_text)
                
            # 把所有页拼成最终给大模型的干货
            # 用两个换行符分隔不同的页面，给 process 引擎一个明确的段落暗示
            extracted_text = "\n\n".join(clean_text_blocks)
            
        else:
            return {"status": "error", "message": f"暂不支持 {file_extension} 格式解析"}

        # 3. 拦截空内容（防御扫描版 PDF）
        if not extracted_text.strip():
            return {"status": "error", "message": "无法提取文字，请确保 PDF 不是纯图片扫描件"}
        
        # 5. 将文件内容存入向量数据库中
        await process_and_store_document(
            db=db,
            doc_id=document_id,
            content=extracted_text,
            source=file.filename,
            metadata=meta_data,
            overlap=50,
            chunk_size=500
        )

        # 6. 成功返回
        return {
            "status": "success", 
            "doc_id": document_id,
            "filename": file.filename,
            "message": "文件切片与向量化入库完成"
        }

    except Exception as e:
        # 你提到的外部捕获：由于 db 是在路由层注入的，发生异常时需向上抛出，或在此处直接触发回滚
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    

# 获取已上传的文件列表
@router.get("/documents")
async def list_uploaded_documents(db: AsyncSession = Depends(get_db)): 
    """
    获取已上传的文档列表（供前端刷新页面时初始化展示）
    """
    try: 
        # group_by有去重的作用
        stmt = select(
            DocumentChunk.doc_id, 
            DocumentChunk.source_file
        ).group_by(
            DocumentChunk.doc_id, 
            DocumentChunk.source_file
        )

        result = await db.execute(stmt)
        # 提取查询出来的行数据
        rows = result.all()

        # 组装成标准 JSON 格式返回给前端
        documents = [
            {"doc_id": row.doc_id, "filename": row.source_file} 
            for row in rows
        ]

        return {
            "status": "success",
            "data": documents,
            "total": len(documents)
        }

    except Exception as e:
        print(f"❌ 获取文档列表失败: {e}")
        return {"status": "error", "message": "无法获取文档列表", "data": []}


@router.delete("/delete/{doc_id}") 
async def delete_file(doc_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除已经上传的知识库文件及所有相关的向量切片
    """
    try:
        # 1. 构造精确打击的 DELETE 语句
        stmt = delete(DocumentChunk).where(DocumentChunk.doc_id == doc_id)

        # 2. 执行并落盘
        result = await db.execute(stmt)
        await db.commit()

        # 使用 .rowcount 获取真实删除的条数
        deleted_count = result.rowcount

        # 防御编程：如果发现根本没删掉东西（可能早就被删了）
        if deleted_count == 0:
            return {
                "status": "warning", 
                "message": "未找到对应的文档，可能已被删除"
            }

        return {
            "status": "success",
            "message": f"文档彻底销毁！共清理了 {deleted_count} 个向量切片。",
            "deleted_chunks": deleted_count
        }

    except Exception as e:
        # 🌟 最棒的一点：你记住了发生异常必须回滚！
        await db.rollback()
        print(f"❌ 文件删除失败: {e}") # 修正文案
        return {"status": "error", "message": "服务器异常，文件删除失败"}