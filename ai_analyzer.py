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


def analyze_customer(customer):
    """
    使用 DeepSeek 分析单个客户
    """

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

    if not result_text:
        raise ValueError("AI返回内容为空")

    result_text = result_text.strip()

    # 清理 Markdown JSON 代码块
    if result_text.startswith("```json"):
        result_text = result_text[7:]

    elif result_text.startswith("```"):
        result_text = result_text[3:]

    if result_text.endswith("```"):
        result_text = result_text[:-3]

    result_text = result_text.strip()

    result = json.loads(result_text)

    return result