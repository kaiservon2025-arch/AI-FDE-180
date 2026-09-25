import os
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# 读取环境变量
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 读取客户Excel
df = pd.read_excel("customers.xlsx")

results = []

for index, row in df.iterrows():

    print(f"正在分析：{row['公司']}")

    customer = {
        "company": row["公司"],
        "country": row["国家"],
        "employees": row["员工数量"],
        "industry": row["行业"],
        "website": row["网站"]
    }

    prompt = f"""
请分析下面这个外贸客户，并严格按照 JSON 格式输出。

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

    try:
        result = json.loads(result_text)

        results.append({
            "公司": row["公司"],
            "国家": row["国家"],
            "行业": row["行业"],
            "员工数量": row["员工数量"],
            "网站": row["网站"],
            "客户等级": result["customer_level"],
            "客户评分": result["customer_score"],
            "客户画像": result["customer_profile"],
            "可能需求": "\n".join(result["possible_needs"]),
            "开发策略": result["development_strategy"],
            "邮件主题": result["email_subject"],
            "邮件正文": result["email_body"]
        })

        print("分析完成")

    except Exception as e:
        print("JSON解析失败：", e)

print("===================")

result_df = pd.DataFrame(results)

result_df.to_excel(
    "day5_customer_analysis.xlsx",
    index=False
)

print("全部完成")
print("生成文件：day5_customer_analysis.xlsx")