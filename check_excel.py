import pandas as pd

df = pd.read_excel("customers.xlsx")

print("Excel列名：")
print(df.columns.tolist())

print("\n第一条客户数据：")
print(df.iloc[0])