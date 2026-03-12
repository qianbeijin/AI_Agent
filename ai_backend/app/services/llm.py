from openai import AsyncOpenAI
from app.core.config import settings
from typing import AsyncGenerator, List

# 实例化客户端
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_URL
)

async def get_deepseek_response(messages: List[dict]) -> AsyncGenerator[str, None]:
    """
    发送对话历史给 DeepSeek
    :param messages: [{"role": "user", "content": "..."}, ...]
    """
    try:
        response = await client.chat.completions.create(  
            model="deepseek-chat", # 或者 deepseek-coder
            messages=messages,
            temperature=0.7,
            stream=True # 开启流式开关
        )
        # 异步遍历流中的每一个片段 (Chunk)
        async for chunk in response:
            # 提取当前片段的文字内容
            content = chunk.choices[0].delta.content
            if content:
                yield content  # 👈 关键：每产生一个字就吐出去
    except Exception as e:
        print(f"Error calling DeepSeek: {e}")
        yield "AI 大脑掉线了，请稍后再试。"