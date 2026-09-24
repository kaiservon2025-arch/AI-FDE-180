import pandas as pd

# 测试客户数据
customers = [
    {
        "公司": "ABC Electronics",
        "国家": "Germany",
        "行业": "Consumer Electronics",
        "员工数量": 120,
        "网站": "https://example.com"
    },
    {
        "公司": "Shenzhen Tech",
        "国家": "USA",
        "行业": "Electronics",
        "员工数量": 80,
        "网站": "https://example.com"
    },
    {
        "公司": "Global Outdoor",
        "国家": "UK",
        "行业": "Outdoor Products",
        "员工数量": 300,
        "网站": "https://example.com"
    },
    {
        "公司": "Smart Factory",
        "国家": "Germany",
        "行业": "Industrial Equipment",
        "员工数量": 500,
        "网站": "https://example.com"
    },
    {
        "公司": "Asia Components",
        "国家": "France",
        "行业": "Electronic Components",
        "员工数量": 60,
        "网站": "https://example.com"
    }
]

# 转换成表格
df = pd.DataFrame(customers)

# 保存到 Excel
df.to_excel("customers.xlsx", index=False)

print("客户数据创建成功！")
print(f"共创建 {len(df)} 个客户")