import sqlite3
from pathlib import Path

# 数据库文件位置
DB_PATH = Path(__file__).parent / "crm.db"


def init_database():
    print("正在初始化 CRM 数据库...")
    print(f"数据库位置：{DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建企业表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            industry TEXT,
            address TEXT,
            source TEXT,
            status TEXT DEFAULT '新客户',
            ai_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # 查询企业数量
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]

    print(f"当前企业数量：{count}")

    conn.close()

    print("CRM 数据库初始化完成。")


if __name__ == "__main__":
    init_database()