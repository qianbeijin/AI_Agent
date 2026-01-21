from openai import AsyncOpenAI
from app.core.config import settings

# 实例化客户端
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_URL
)

async def get_deepseek_response(userInput: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat", # 或者 deepseek-coder
            messages=[
                {"role": "system", "content": "你是一个专业的AI助手。"},
                {"role": "user", "content": userInput}
            ],
            stream=False # 先做非流式，下周教你做流式(SSE)
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling DeepSeek: {e}")
        return "AI 大脑掉线了，请稍后再试。"