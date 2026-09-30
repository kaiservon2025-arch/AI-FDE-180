import sqlite3

db_path = "database/crm.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO companies (name) VALUES (?)",
    ("测试企业",)
)

conn.commit()

print("写入成功！")

cursor.execute("SELECT * FROM companies")
companies = cursor.fetchall()

print("当前企业：")
for company in companies:
    print(company)

conn.close()