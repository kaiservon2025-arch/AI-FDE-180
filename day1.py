customer_name = "ABC Electronics"
industry = "Consumer Electronics"
country = "Germany"
employees = 120

print("===== 客户信息 =====")
print("客户名称：", customer_name)
print("行业：", industry)
print("国家：", country)
print("员工数量：", employees)

print("\n===== FDE 初步分析 =====")

if employees >= 100 and industry == "Consumer Electronics":
    print("客户规模：中大型")
    print("行业匹配：是")
    print("开发建议：重点开发")
else:
    print("开发建议：进一步研究")