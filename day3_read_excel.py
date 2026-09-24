import pandas as pd

# 读取客户 Excel
df = pd.read_excel("customers.xlsx")

print("===== 客户数据 =====")
print(df)

print("\n===== 客户数量 =====")
print(len(df))

print("\n===== 逐个读取客户 =====")

for index, customer in df.iterrows():
    print("\n--------------------")
    print("公司：", customer["公司"])
    print("国家：", customer["国家"])
    print("行业：", customer["行业"])
    print("员工数量：", customer["员工数量"])
    print("网站：", customer["网站"])