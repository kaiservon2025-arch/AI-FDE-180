from lead_contact_search import (
    search_company_contacts
)

from web_page_scraper import (
    scrape_pages
)

from contact_extractor import (
    extract_contacts_from_pages
)


print("================================")
print("AI-FDE Day 12-4")
print("深度网页联系方式提取")
print("================================")


company_name = (
    "三和盛电子制造（东莞）有限公司"
)


print()
print("第一步：搜索公开网页")
print()


pages_df = search_company_contacts(
    company_name=company_name,
    max_results=5
)


print()
print(
    f"搜索得到 {len(pages_df)} 个网页"
)
print()


if len(pages_df) == 0:

    print(
        "没有搜索结果。"
    )

    raise SystemExit


print("第二步：抓取网页正文")
print()


pages_df = scrape_pages(
    pages_df=pages_df,
    max_pages=20
)


print()
print("第三步：提取联系方式")
print()


contacts_df = extract_contacts_from_pages(
    pages_df
)


print()
print("================================")
print("最终联系方式")
print("================================")
print()


if len(contacts_df) == 0:

    print(
        "没有提取到联系方式。"
    )

else:

    display_columns = [
        "公司",
        "邮箱",
        "电话",
        "联系人",
        "职位",
        "官网域名",
        "信息日期",
        "来源网址",
        "网页抓取成功"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in contacts_df.columns
    ]

    print(
        contacts_df[
            display_columns
        ].to_string(
            index=False
        )
    )


print()
print("================================")
print("统计")
print("================================")
print()


print(
    f"网页数量：{len(pages_df)}"
)

if len(pages_df) > 0:

    success_count = (
        pages_df[
            "网页抓取成功"
        ].sum()
    )

    print(
        f"网页抓取成功：{success_count}"
    )

    print(
        f"网页抓取失败："
        f"{len(pages_df) - success_count}"
    )


print(
    f"联系方式记录：{len(contacts_df)}"
)


if len(contacts_df) > 0:

    email_count = (
        contacts_df["邮箱"]
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    phone_count = (
        contacts_df["电话"]
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    contact_count = (
        contacts_df["联系人"]
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    print(
        f"邮箱：{email_count}"
    )

    print(
        f"电话：{phone_count}"
    )

    print(
        f"联系人：{contact_count}"
    )


print()
print("Day 12-4 测试完成。")