import os
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI


# ======================
# 读取API
# ======================

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)


# ======================
# 读取客户数据
# ======================

df = pd.read_excel("customers.xlsx")


customer = df.iloc[0]


company = customer["公司"]
country = customer["国家"]
industry = customer["行业"]
employees = customer["员工数量"]


print("正在分析客户：", company)


# ======================
# AI销售分析
# ======================

prompt = f"""

你是一名专业B2B销售顾问。

请分析这个潜在客户：

公司：
{company}

国家：
{country}

行业：
{industry}

员工规模：
{employees}


请严格按照以下格式输出：

【客户等级】
A/B/C

【客户画像】
xxx

【可能需求】
xxx

【开发策略】
xxx

【第一封开发邮件主题】
xxx

【第一封开发邮件】
xxx

要求：
1. 面向真实商业开发
2. 简洁专业
3. 不要编造不存在的信息

"""


response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role":"user",
            "content":prompt
        }
    ]
)


result = response.choices[0].message.content


print("\n===== AI销售分析 =====")
print(result)