from lead_search import search_manufacturing_leads
from lead_filter import filter_target_companies


print("================================")
print("AI-FDE Day 11-4")
print("全网企业搜索 + AI企业筛选")
print("================================")


print()
print("第一步：搜索互联网...")
print()


leads_df = search_manufacturing_leads(
    province="广东",
    city="东莞",
    industry="电子制造",
    keyword="",
    limit=40
)


print()
print("================================")
print("搜索阶段完成")
print("================================")

print()

print(
    f"搜索得到 {len(leads_df)} 条网页结果"
)

print()


if len(leads_df) == 0:

    print("没有搜索结果。")

    raise SystemExit


print("第二步：AI筛选全部搜索结果...")
print()


target_df = filter_target_companies(
    leads_df=leads_df,
    province="广东",
    city="东莞",
    industry="电子制造"
)


print()
print("================================")
print("最终企业名单")
print("================================")
print()


if len(target_df) == 0:

    print("没有找到符合条件的企业。")

else:

    display_columns = [
        "公司",
        "省份",
        "城市",
        "行业",
        "AI判断",
        "AI判断原因",
        "来源网址"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in target_df.columns
    ]

    print(
        target_df[
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
    f"网页结果：{len(leads_df)} 条"
)

print(
    f"目标企业：{len(target_df)} 家"
)

print()

print("Day 11-4 测试完成。")