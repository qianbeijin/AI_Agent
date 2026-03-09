import httpx
from app.core.config import settings

# 硅基流动 API 地址
SILICONFLOW_URL = "https://api.siliconflow.cn/v1/embeddings"

async def get_embedding(text: str) -> list[float]:
    """
    调用硅基流动 API 将文本转换为向量
    """
    # headers固定写法, settings.EMBEDDING_API_KEY获取配置文件中的秘钥
    headers = {
        "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "BAAI/bge-m3", # 确保和你灌装时用的是同一个！（业界最强开源中文向量模型）
        "input": '测试111',
        "encoding_format": "float"
    }

    # 使用 async with 可确保：请求结束后自动关闭; 连接释放内存和网络资源; 避免连接泄漏（尤其在高并发场景）
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SILICONFLOW_URL,
                json = payload,
                headers = headers,
                timeout = 10.0 # 设置 10 秒超时，防止网络卡死
            )

            # 这里的作用是抛出状态码，如果状态码异常则会抛出错误，如果状态码正常，则什么都不会发生
            response.raise_for_status()

            # http返回的通常是文本，虽然看起来像list或dist，因此需要将其转化为list或dict
            data = response.json()

            # 核心：从返回的嵌套字典中提取出那串 1024 维的数字
            # 返回格式通常是：{"data": [{"embedding": [...]}]}
            return data["data"][0]["embedding"]

        except httpx.HTTPStatusError as e:
            #   HTTP 状态码（比如 401 密钥错误，402 没钱了, 503 硅基服务暂时不可用）
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
