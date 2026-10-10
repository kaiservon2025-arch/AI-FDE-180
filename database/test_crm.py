import sqlite3

db_path = "database/crm.db"


def add_company():
    name = input("企业名称：").strip()
    contact = input("联系人：").strip()
    phone = input("电话：").strip()
    email = input("邮箱：").strip()
    website = input("官网：").strip()
    industry = input("行业：").strip()
    address = input("地址：").strip()
    source = input("来源：").strip()

    if not name:
        print("企业名称不能为空！")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查企业是否已经存在
    cursor.execute(
        "SELECT id FROM companies WHERE name = ?",
        (name,)
    )

    existing = cursor.fetchone()

    if existing:
        print(f"企业「{name}」已经存在，ID：{existing[0]}")
        conn.close()
        return

    # 写入企业
    cursor.execute(
        """
        INSERT INTO companies
        (name, contact, phone, email, website, industry, address, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            contact,
            phone,
            email,
            website,
            industry,
            address,
            source
        )
    )

    conn.commit()

    company_id = cursor.lastrowid

    print(f"\n企业添加成功！")
    print(f"企业ID：{company_id}")
    print(f"企业名称：{name}")

    conn.close()


def list_companies():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, contact, phone, industry, source, status
        FROM companies
        ORDER BY id
        """
    )

    companies = cursor.fetchall()

    print("\n========== CRM企业列表 ==========")

    if not companies:
        print("暂无企业")
    else:
        for company in companies:
            print(
                f"ID：{company[0]} | "
                f"企业：{company[1]} | "
                f"联系人：{company[2]} | "
                f"电话：{company[3]} | "
                f"行业：{company[4]} | "
                f"来源：{company[5]} | "
                f"状态：{company[6]}"
            )

    conn.close()


def main():
    print("========== AI-FDE CRM ==========")
    print("1. 新增企业")
    print("2. 查看企业")

    choice = input("请选择功能：").strip()

    if choice == "1":
        add_company()
    elif choice == "2":
        list_companies()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()