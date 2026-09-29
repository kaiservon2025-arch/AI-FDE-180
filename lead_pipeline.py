import pandas as pd

from lead_search import (
    search_manufacturing_leads
)

from lead_filter import (
    filter_target_companies
)

from lead_contact_search import (
    search_company_contacts
)

from web_page_scraper import (
    scrape_pages
)

from contact_extractor import (
    extract_contacts_from_pages
)

from contact_validator import (
    validate_contacts
)


def run_lead_pipeline(
    province="广东",
    city="东莞",
    industry="电子制造",
    keyword="",
    company_limit=5
):
    """
    AI-FDE完整企业获客流程。

    搜索企业
    → AI筛选企业
    → 搜索企业联系方式
    → 抓取网页
    → 提取联系方式
    → AI验证联系方式
    """

    print()
    print("================================")
    print("AI-FDE 自动获客系统")
    print("================================")
    print()

    # =================================
    # 第一步：搜索企业
    # =================================

    print("【1/6】搜索目标企业")
    print()

    leads_df = search_manufacturing_leads(
        province=province,
        city=city,
        industry=industry,
        keyword=keyword,
        limit=company_limit
    )

    if len(leads_df) == 0:

        print("没有搜索到企业。")

        return pd.DataFrame()

    print()
    print(
        f"搜索到 {len(leads_df)} 条企业结果。"
    )

    # =================================
    # 第二步：AI筛选企业
    # =================================

    print()
    print("【2/6】AI筛选目标企业")
    print()

    filtered_df = filter_target_companies(
        leads_df
    )

    if len(filtered_df) == 0:

        print("没有找到符合条件的目标企业。")

        return pd.DataFrame()

    # 限制企业数量
    filtered_df = (
        filtered_df
        .head(company_limit)
        .copy()
    )

    print()
    print(
        f"最终目标企业：{len(filtered_df)} 家"
    )

    # =================================
    # 第三步：搜索企业公开联系方式网页
    # =================================

    print()
    print("【3/6】搜索企业公开联系方式")
    print()

    all_pages = []

    for index, row in filtered_df.iterrows():

        company = str(
            row.get("公司", "")
        )

        if not company:
            continue

        print()
        print(
            f"正在搜索：{company}"
        )

        try:

            pages_df = search_company_contacts(
                company_name=company,
                max_results=5
            )

            if len(pages_df) > 0:

                pages_df["公司"] = company

                all_pages.append(
                    pages_df
                )

                print(
                    f"找到 {len(pages_df)} 个网页"
                )

            else:

                print(
                    "没有找到公开网页。"
                )

        except Exception as e:

            print(
                f"搜索失败：{e}"
            )

    if not all_pages:

        print()
        print(
            "没有找到企业联系方式网页。"
        )

        return pd.DataFrame()

    pages_df = pd.concat(
        all_pages,
        ignore_index=True
    )

    # =================================
    # 第四步：抓取网页正文
    # =================================

    print()
    print("【4/6】抓取网页正文")
    print()

    pages_df = scrape_pages(
        pages_df=pages_df,
        max_pages=50
    )

    # =================================
    # 第五步：提取联系方式
    # =================================

    print()
    print("【5/6】提取联系方式")
    print()

    contacts_df = extract_contacts_from_pages(
        pages_df
    )

    if len(contacts_df) == 0:

        print()
        print(
            "没有提取到联系方式。"
        )

        return pd.DataFrame()

    # =================================
    # 第六步：AI验证联系方式
    # =================================

    print()
    print("【6/6】AI验证联系方式")
    print()

    validated_df = validate_contacts(
        contacts_df
    )

    print()
    print("================================")
    print("AI-FDE获客流程完成")
    print("================================")
    print()

    print(
        f"最终联系方式："
        f"{len(validated_df)} 条"
    )

    if len(validated_df) > 0:

        high_confidence = (
            validated_df[
                "AI可信度"
            ]
            .astype(str)
            .eq("高")
            .sum()
        )

        relevant = (
            validated_df[
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

    return validated_df


if __name__ == "__main__":

    result_df = run_lead_pipeline(
        province="广东",
        city="东莞",
        industry="电子制造",
        keyword="",
        company_limit=3
    )

    print()
    print("================================")
    print("最终结果")
    print("================================")
    print()

    if len(result_df) == 0:

        print(
            "没有产生最终销售线索。"
        )

    else:

        columns = [
            "公司",
            "邮箱",
            "电话",
            "联系人",
            "职位",
            "AI联系方式类型",
            "AI是否适合HR销售",
            "AI信息新鲜度",
            "AI可信度",
            "AI判断理由",
            "来源网址"
        ]

        columns = [
            column
            for column in columns
            if column in result_df.columns
        ]

        print(
            result_df[
                columns
            ].to_string(
                index=False
            )
        )