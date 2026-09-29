import os
import json
import pandas as pd

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)

DEEPSEEK_BASE_URL = (
    "https://api.deepseek.com"
)


def get_client():
    """
    创建 DeepSeek 客户端。
    """

    if not DEEPSEEK_API_KEY:

        raise ValueError(
            "没有找到 DEEPSEEK_API_KEY，请检查 .env 文件。"
        )

    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )


def validate_contact(
    company,
    email="",
    phone="",
    contact_name="",
    job_title="",
    information_date="",
    source_url="",
    page_title="",
    page_content=""
):
    """
    使用 DeepSeek 判断联系方式是否可信，
    以及是否适合后续销售开发。
    """

    client = get_client()

    prompt = f"""
你是一名B2B销售线索验证专家。

现在需要验证一条企业联系方式。

目标企业：
{company}

联系人：
{contact_name}

职位：
{job_title}

邮箱：
{email}

电话：
{phone}

信息日期：
{information_date}

网页标题：
{page_title}

来源网址：
{source_url}

网页内容：
{page_content[:5000]}

请根据这些公开信息进行判断。

重点判断：

1. 这个联系方式是否大概率属于目标企业？
2. 联系方式属于什么类型？
3. 是否可能与HR、人力资源、招聘、行政或企业采购相关？
4. 信息的新鲜程度如何？
5. 联系方式可信度如何？

联系方式类型只能选择：

- HR/人事
- 招聘
- 企业管理
- 销售
- 客服
- 公司总机
- 企业采购
- 其他
- 未知

信息新鲜度只能选择：

- 新
- 较新
- 较旧
- 未知

可信度只能选择：

- 高
- 中
- 低

请严格返回JSON，不要输出其他文字。

JSON格式：

{{
    "is_company_contact": true,
    "contact_type": "HR/人事",
    "is_relevant_for_hr_sales": true,
    "freshness": "新",
    "confidence": "高",
    "reason": "判断理由"
}}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一名专业的B2B销售线索验证AI。"
                    "必须严格按照要求返回JSON。"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    content = content.strip()

    # 处理 DeepSeek 偶尔返回 ```json ... ```
    if content.startswith("```"):

        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        )

        content = content.strip()

    try:

        result = json.loads(content)

    except json.JSONDecodeError:

        result = {
            "is_company_contact": False,
            "contact_type": "未知",
            "is_relevant_for_hr_sales": False,
            "freshness": "未知",
            "confidence": "低",
            "reason": (
                "AI返回结果无法解析"
            )
        }

    return result


def validate_contacts(
    contacts_df
):
    """
    批量验证联系方式。
    """

    if contacts_df is None:

        raise ValueError(
            "联系方式数据为空。"
        )

    if len(contacts_df) == 0:

        return pd.DataFrame()

    print()
    print("================================")
    print("AI联系方式验证")
    print("================================")
    print()

    results = []

    total = len(contacts_df)

    for index, row in contacts_df.iterrows():

        company = str(
            row.get("公司", "")
        )

        email = str(
            row.get("邮箱", "")
        )

        phone = str(
            row.get("电话", "")
        )

        contact_name = str(
            row.get("联系人", "")
        )

        job_title = str(
            row.get("职位", "")
        )

        information_date = str(
            row.get("信息日期", "")
        )

        source_url = str(
            row.get("来源网址", "")
        )

        page_title = str(
            row.get("网页标题", "")
        )

        print(
            f"[{index + 1}/{total}] "
            f"{company}"
        )

        print(
            f"  邮箱：{email}"
        )

        print(
            f"  电话：{phone}"
        )

        try:

            result = validate_contact(
                company=company,
                email=email,
                phone=phone,
                contact_name=contact_name,
                job_title=job_title,
                information_date=information_date,
                source_url=source_url,
                page_title=page_title
            )

            row_data = row.to_dict()

            row_data.update(
                {
                    "AI是否属于目标公司":
                        result.get(
                            "is_company_contact",
                            False
                        ),

                    "AI联系方式类型":
                        result.get(
                            "contact_type",
                            "未知"
                        ),

                    "AI是否适合HR销售":
                        result.get(
                            "is_relevant_for_hr_sales",
                            False
                        ),

                    "AI信息新鲜度":
                        result.get(
                            "freshness",
                            "未知"
                        ),

                    "AI可信度":
                        result.get(
                            "confidence",
                            "低"
                        ),

                    "AI判断理由":
                        result.get(
                            "reason",
                            ""
                        )
                }
            )

            results.append(
                row_data
            )

            print(
                f"  → 类型："
                f"{result.get('contact_type', '未知')}"
            )

            print(
                f"  → 新鲜度："
                f"{result.get('freshness', '未知')}"
            )

            print(
                f"  → 可信度："
                f"{result.get('confidence', '低')}"
            )

        except Exception as e:

            print(
                f"  → AI验证失败：{e}"
            )

            row_data = row.to_dict()

            row_data.update(
                {
                    "AI是否属于目标公司":
                        False,

                    "AI联系方式类型":
                        "未知",

                    "AI是否适合HR销售":
                        False,

                    "AI信息新鲜度":
                        "未知",

                    "AI可信度":
                        "低",

                    "AI判断理由":
                        f"验证失败：{e}"
                }
            )

            results.append(
                row_data
            )

    result_df = pd.DataFrame(
        results
    )

    print()
    print("================================")
    print("AI联系方式验证完成")
    print("================================")
    print()

    print(
        f"验证数量：{len(result_df)}"
    )

    if len(result_df) > 0:

        high_confidence = (
            result_df[
                "AI可信度"
            ]
            .astype(str)
            .eq("高")
            .sum()
        )

        relevant = (
            result_df[
                "AI是否适合HR销售"
            ]
            .astype(str)
            .str.lower()
            .eq("true")
            .sum()
        )

        print(
            f"高可信联系方式："
            f"{high_confidence}"
        )

        print(
            f"适合HR销售："
            f"{relevant}"
        )

    return result_df