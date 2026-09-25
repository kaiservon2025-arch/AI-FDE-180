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

# 读取 Day 5 的客户分析结果
df = pd.read_excel("day5_customer_analysis.xlsx")

results = []

for index, row in df.iterrows():

    print(f"正在生成销售行动：{row['公司']}")

    customer_info = {
        "公司": row["公司"],
        "国家": row["国家"],
        "行业": row["行业"],
        "员工数量": row["员工数量"],
        "网站": row["网站"],
        "客户等级": row["客户等级"],
        "客户评分": row["客户评分"],
        "客户画像": row["客户画像"],
        "可能需求": row["可能需求"],
        "开发策略": row["开发策略"]
    }

    prompt = f"""
你是一名B2B外贸销售顾问。

请根据下面的客户信息，制定具体的销售行动计划。

客户信息：
{customer_info}

请严格按照 JSON 格式输出以下字段：

priority
reason
recommended_action
follow_up_days
follow_up_focus

要求：

1. priority：高、中、低
2. reason：说明为什么应该优先开发或暂缓
3. recommended_action：销售人员下一步应该做什么
4. follow_up_days：建议多少天后跟进，必须是整数
5. follow_up_focus：下一次跟进应该重点确认什么

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
            "客户评分": row["客户评分"],
            "客户等级": row["客户等级"],
            "AI优先级": result["priority"],
            "开发理由": result["reason"],
            "推荐销售动作": result["recommended_action"],
            "建议跟进天数": result["follow_up_days"],
            "跟进重点": result["follow_up_focus"]
        })

        print("生成完成")

    except Exception as e:

        print("JSON解析失败：", e)

print("===================")

result_df = pd.DataFrame(results)

result_df.to_excel(
    "day6_ai_sales_action.xlsx",
    index=False
)

print("全部完成")
print("生成文件：day6_ai_sales_action.xlsx")