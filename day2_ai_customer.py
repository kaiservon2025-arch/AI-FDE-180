import os 
print("程序开始运行")
from dotenv import load_dotenv
from openai import OpenAI


# 加载环境变量
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
print("API Key状态：", "已读取" if api_key else "未读取")

# 创建客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)


# 请求AI分析
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "user",
            "content": """
            请分析下面这个客户：

            公司：Romaguera-Crona
            国家：德国
            行业：消费电子

            输出：
            1. 客户画像
            2. 潜在需求
            3. 是否值得开发
            4. 开发建议
            """
        }
    ]
)


print(response.choices[0].message.content)