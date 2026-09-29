from lead_contact_search import (
    search_company_contacts
)

from web_page_scraper import (
    scrape_pages
)


print("================================")
print("AI-FDE Day 12-3")
print("公开网页正文抓取测试")
print("================================")


company_name = (
    "三和盛电子制造（东莞）有限公司"
)


print()
print("第一步：搜索企业公开网页")
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
        "没有搜索结果，测试结束。"
    )

    raise SystemExit


print("第二步：抓取网页正文")
print()


scraped_df = scrape_pages(
    pages_df=pages_df,
    max_pages=10
)


print()
print("================================")
print("抓取结果")
print("================================")
print()


if len(scraped_df) == 0:

    print(
        "没有抓取结果。"
    )

else:

    for index, row in scraped_df.iterrows():

        print("--------------------------------")

        print(
            f"网页 {index + 1}"
        )

        print(
            "网址：",
            row.get(
                "网址",
                ""
            )
        )

        print(
            "网页标题：",
            row.get(
                "网页标题",
                ""
            )
        )

        print(
            "抓取成功：",
            row.get(
                "网页抓取成功",
                False
            )
        )

        print(
            "正文字符数：",
            len(
                str(
                    row.get(
                        "网页正文",
                        ""
                    )
                )
            )
        )

        text = str(
            row.get(
                "网页正文",
                ""
            )
        )

        if len(text) > 500:

            text = text[:500] + "..."

        print(
            "正文预览：",
            text
        )


print()
print("================================")
print("统计")
print("================================")
print()


if len(scraped_df) > 0:

    success_count = (
        scraped_df[
            "网页抓取成功"
        ].sum()
    )

    print(
        f"网页数量：{len(scraped_df)}"
    )

    print(
        f"抓取成功：{success_count}"
    )

    print(
        f"抓取失败："
        f"{len(scraped_df) - success_count}"
    )


print()
print("Day 12-3 测试完成。")