import os
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI

# 读取 API Key
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

# 创建 AI 客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 读取 Excel
df = pd.read_excel("customers.xlsx")

# 获取第一个客户
customer = df.iloc[0]

company = customer["公司"]
country = customer["国家"]
industry = customer["行业"]
employees = customer["员工数量"]

print("正在分析客户：", company)

# 发送给 AI
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "user",
            "content": f"""
请分析下面这个外贸潜在客户：

公司：{company}
国家：{country}
行业：{industry}
员工数量：{employees}

请输出：

1. 客户画像
2. 潜在需求
3. 是否值得开发
4. 开发建议

请用中文回答，简洁、具体。
"""
        }
    ]
)

# 输出 AI 分析结果
result = response.choices[0].message.content

print("\n===== AI客户分析结果 =====")
print(result)