import os
import json
from dotenv import load_dotenv
from openai import OpenAI


# ==============================
# 加载环境变量
# ==============================

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")


# ==============================
# 创建DeepSeek客户端
# ==============================

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)


# ==============================
# AI客户分析
# ==============================

def analyze_customer(customer):

    prompt = f"""
请分析下面这个外贸客户，并严格按照 JSON 格式输出。

客户信息：

{customer}

必须包含以下7个字段：

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
4. possible_needs：客户可能的需求，必须使用数组
5. development_strategy：开发策略
6. email_subject：英文开发邮件主题
7. email_body：英文开发邮件正文

非常重要：

必须保留以上7个字段。

即使某项无法判断，也不能删除字段。

只输出标准 JSON。

不要输出 Markdown。

不要输出 ```json。

不要输出任何解释。

JSON格式必须类似：

{{
    "customer_level": "A",
    "customer_score": 80,
    "customer_profile": "客户画像",
    "possible_needs": [
        "需求1",
        "需求2"
    ],
    "development_strategy": "开发策略",
    "email_subject": "英文邮件主题",
    "email_body": "英文邮件正文"
}}
"""


    # ==============================
    # 调用DeepSeek
    # ==============================

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


    # ==============================
    # 获取AI返回内容
    # ==============================

    result_text = response.choices[0].message.content


    if not result_text:

        raise ValueError(
            "AI返回内容为空"
        )


    result_text = result_text.strip()


    # ==============================
    # 清理Markdown代码块
    # ==============================

    if result_text.startswith("```json"):

        result_text = result_text[7:]

    elif result_text.startswith("```"):

        result_text = result_text[3:]


    if result_text.endswith("```"):

        result_text = result_text[:-3]


    result_text = result_text.strip()


    # ==============================
    # JSON解析
    # ==============================

    try:

        result = json.loads(
            result_text
        )

    except json.JSONDecodeError as e:

        raise ValueError(
            f"AI返回的内容不是有效JSON：{e}\n"
            f"AI原始返回：{result_text}"
        )


    # ==============================
    # 防止AI缺少字段
    # ==============================

    result.setdefault(
        "customer_level",
        "C"
    )

    result.setdefault(
        "customer_score",
        0
    )

    result.setdefault(
        "customer_profile",
        ""
    )

    result.setdefault(
        "possible_needs",
        []
    )

    result.setdefault(
        "development_strategy",
        ""
    )

    result.setdefault(
        "email_subject",
        ""
    )

    result.setdefault(
        "email_body",
        ""
    )


    # ==============================
    # 返回结果
    # ==============================

    return result