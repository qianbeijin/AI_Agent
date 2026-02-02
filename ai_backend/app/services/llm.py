from openai import AsyncOpenAI
from app.core.config import settings
from typing import List

# 实例化客户端
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_URL
)

async def get_deepseek_response(messages: List[dict]) -> str:
    """
    发送对话历史给 DeepSeek
    :param messages: [{"role": "user", "content": "..."}, ...]
    """
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat", # 或者 deepseek-coder
            messages=messages,
            temperature=0.7,
            stream=False # 非流式
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling DeepSeek: {e}")
        return "AI 大脑掉线了，请稍后再试。"