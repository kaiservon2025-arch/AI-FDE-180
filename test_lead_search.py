from lead_search import search_manufacturing_leads


print("开始测试制造业企业搜索模块...")


leads_df = search_manufacturing_leads(
    province="广东",
    city="",
    industry="电子制造",
    keyword="",
    limit=20
)


print()
print("搜索完成")
print()
print(leads_df.to_string(index=False))


print()
print(f"共找到 {len(leads_df)} 家企业")