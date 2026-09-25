import os
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI


# ======================
# 1. 读取 API Key
# ======================

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)


# ======================
# 2. 读取客户文件
# ======================

df = pd.read_excel("customers.xlsx")

print("客户数量：", len(df))


results = []


# ======================
# 3. 循环分析客户
# ======================

for index, customer in df.iterrows():

    company = customer["公司"]
    country = customer["国家"]
    industry = customer["行业"]
    employees = customer["员工数量"]

    print("\n正在分析：", company)


    prompt = f"""

你是一名专业B2B销售顾问。

分析下面客户：

公司：
{company}

国家：
{country}

行业：
{industry}

员工规模：
{employees}


请严格按照以下格式输出：

客户等级：
(A/B/C)

客户评分：
(0-100)

客户画像：
xxx

可能需求：
xxx

开发策略：
xxx

邮件主题：
xxx

开发邮件：
xxx

要求：
1. 中文回答分析部分
2. 邮件使用英文
3. 不要编造客户不存在的信息
4. 针对B2B销售场景
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


    results.append(result)

    print("分析完成")


# ======================
# 4. 保存结果
# ======================

df["AI销售分析"] = results


df.to_excel(
    "sales_analysis_result.xlsx",
    index=False
)


print("\n===================")
print("全部完成")
print("生成文件：sales_analysis_result.xlsx")