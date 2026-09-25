import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

customer = {
    "company": "ABC Electronics",
    "country": "Germany",
    "employees": 120,
    "industry": "Consumer Electronics"
}

prompt = f"""
请分析下面这个客户，并严格按照 JSON 格式输出。

客户信息：
{customer}

必须包含以下字段：
customer_level
customer_score
customer_profile
possible_needs
development_strategy
email_subject
email_body

要求：
1. customer_level：A、B、C 三个等级之一
2. customer_score：0-100 的整数
3. customer_profile：客户画像
4. possible_needs：客户可能的需求，使用数组
5. development_strategy：开发策略
6. email_subject：英文开发邮件主题
7. email_body：英文开发邮件正文

只输出 JSON，不要输出其他解释。
"""

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

result_text = response.choices[0].message.content

print("===== AI原始输出 =====")
print(result_text)

print("\n===== Python解析后的数据 =====")

result = json.loads(result_text)

print("客户等级：", result["customer_level"])
print("客户评分：", result["customer_score"])
print("客户画像：", result["customer_profile"])
print("客户需求：", result["possible_needs"])
print("开发策略：", result["development_strategy"])
print("邮件主题：", result["email_subject"])
print("邮件正文：", result["email_body"])