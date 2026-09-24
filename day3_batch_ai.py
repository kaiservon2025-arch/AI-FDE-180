import os
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI

# =========================
# 1. 读取 API Key
# =========================

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# =========================
# 2. 读取 Excel
# =========================

df = pd.read_excel("customers.xlsx")

print("===== AI 批量客户分析系统 =====")
print("客户数量：", len(df))

# 保存 AI 分析结果
results = []

# =========================
# 3. 循环分析每一个客户
# =========================

for index, customer in df.iterrows():

    company = customer["公司"]
    country = customer["国家"]
    industry = customer["行业"]
    employees = customer["员工数量"]

    print("\n----------------------------")
    print(f"正在分析：{company}")
    print(f"进度：{index + 1}/{len(df)}")

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

    result = response.choices[0].message.content

    results.append(result)

    print("AI分析完成")

# =========================
# 4. 把结果写入 Excel
# =========================

df["AI分析结果"] = results

df.to_excel("customer_analysis_result.xlsx", index=False)

print("\n============================")
print("全部客户分析完成！")
print("结果文件：customer_analysis_result.xlsx")