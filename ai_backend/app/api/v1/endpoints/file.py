import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, HTTPException, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ingestion import process_and_store_document

router = APIRouter()

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

    try:
        # 4. 读取文件内容 (跨越二进制空间)
        content_bytes = await file.read()
        raw_text = content_bytes.decode("utf-8") # 此处简化，实际生产需根据文件类型使用 pdfplumber 等解析
        
        # 5. 将文件内容存入向量数据库中
        await process_and_store_document(
            db=db,
            doc_id=document_id,
            content=raw_text,
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