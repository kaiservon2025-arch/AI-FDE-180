from lead_contact_search import (
    search_company_contacts
)


print("================================")
print("AI-FDE Day 12-1")
print("企业全网联系方式搜索测试")
print("================================")


company_name = (
    "三和盛电子制造（东莞）有限公司"
)


results_df = search_company_contacts(
    company_name=company_name,
    max_results=5
)


print()
print("================================")
print("搜索结果")
print("================================")
print()


if len(results_df) == 0:

    print("没有找到公开网页。")

else:

    display_columns = [
        "公司",
        "搜索关键词",
        "标题",
        "网址",
        "信息日期",
        "来源"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in results_df.columns
    ]

    print(
        results_df[
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
    f"最终找到 {len(results_df)} 个公开网页"
)

print()

print("Day 12-1 测试完成。")