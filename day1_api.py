import requests

# 获取客户列表
url = "https://jsonplaceholder.typicode.com/users"

response = requests.get(url)
customers = response.json()

print("===== AI FDE 客户分析系统 =====")

for customer in customers:

    name = customer["name"]
    email = customer["email"]
    company = customer["company"]["name"]

    # 简单客户分类规则
    if len(company) > 15:
        level = "重点客户"
    else:
        level = "普通客户"

    print("\n--------------------")
    print("客户：", name)
    print("邮箱：", email)
    print("公司：", company)
    print("客户等级：", level)