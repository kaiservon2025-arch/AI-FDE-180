import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).parent / "crm.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # ==============================
    # CRM 企业表
    # ==============================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            contact_page TEXT,
            jobs_page TEXT,
            news TEXT,
            source TEXT,
            first_found_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        )
    """)

    # ==============================
    # 搜索发现记录表
    # ==============================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            url TEXT,
            title TEXT,
            source TEXT,
            discovered_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==============================
    # 客户跟进记录表
    # ==============================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            follow_up_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            method TEXT,
            content TEXT,
            next_follow_up_time TIMESTAMP,
            FOREIGN KEY (company_id)
                REFERENCES companies(id)
        )
    """)

    conn.commit()
    conn.close()

    print(
        f"CRM 数据库初始化完成：{DB_PATH}"
    )


# ==================================================
# 企业管理
# ==================================================


def add_company(
    company_name,
    contact=None,
    phone=None,
    email=None,
    address=None,
    contact_page=None,
    jobs_page=None,
    news=None,
    source=None,
    first_found_time=None,
    status="new"
):
    init_database()

    if first_found_time is None:
        first_found_time = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM companies WHERE company_name = ?",
        (company_name,)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()

        return {
            "success": False,
            "message": f"企业「{company_name}」已经存在",
            "company_id": existing[0]
        }

    cursor.execute("""
        INSERT INTO companies (
            company_name,
            contact,
            phone,
            email,
            address,
            contact_page,
            jobs_page,
            news,
            source,
            first_found_time,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company_name,
        contact,
        phone,
        email,
        address,
        contact_page,
        jobs_page,
        news,
        source,
        first_found_time,
        status
    ))

    conn.commit()

    company_id = cursor.lastrowid

    conn.close()

    return {
        "success": True,
        "message": f"企业「{company_name}」添加成功",
        "company_id": company_id
    }


def add_company_record(record):
    """
    将 CompanyRecord 写入 CRM。
    """

    return add_company(
        company_name=record.company_name,
        contact=record.contact,
        phone=record.phone,
        email=record.email,
        address=record.address,
        contact_page=record.contact_page,
        jobs_page=record.jobs_page,
        news=record.news,
        source=record.source,
        first_found_time=record.first_found_time,
        status=record.status
    )


def get_company(company_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company_name,
            contact,
            phone,
            email,
            address,
            contact_page,
            jobs_page,
            news,
            source,
            first_found_time,
            status
        FROM companies
        WHERE id = ?
    """, (company_id,))

    company = cursor.fetchone()

    conn.close()

    return company


def list_companies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company_name,
            contact,
            phone,
            email,
            address,
            contact_page,
            jobs_page,
            news,
            source,
            first_found_time,
            status
        FROM companies
        ORDER BY id
    """)

    companies = cursor.fetchall()

    conn.close()

    return companies


# ==================================================
# 客户状态
# ==================================================


def update_company_status(company_id, status):
    """
    修改客户状态。

    可用状态：

    new         新客户
    contacted   已联系
    replied     已回复
    follow_up   待跟进
    won         已成交
    lost        已流失
    """

    allowed_statuses = {
        "new",
        "contacted",
        "replied",
        "follow_up",
        "won",
        "lost"
    }

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": f"无效客户状态：{status}"
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE companies
        SET status = ?
        WHERE id = ?
        """,
        (status, company_id)
    )

    conn.commit()

    updated_rows = cursor.rowcount

    conn.close()

    if updated_rows == 0:
        return {
            "success": False,
            "message": f"没有找到企业 ID：{company_id}"
        }

    return {
        "success": True,
        "message": f"企业 ID {company_id} 状态已更新为：{status}"
    }


# ==================================================
# 客户跟进
# ==================================================


def add_follow_up(
    company_id,
    method,
    content,
    next_follow_up_time=None,
    follow_up_time=None
):
    """
    添加一次客户跟进记录。

    method 示例：

    email
    phone
    wechat
    meeting
    other
    """

    init_database()

    if follow_up_time is None:
        follow_up_time = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    # 确认企业存在
    cursor.execute(
        """
        SELECT id, company_name
        FROM companies
        WHERE id = ?
        """,
        (company_id,)
    )

    company = cursor.fetchone()

    if company is None:
        conn.close()

        return {
            "success": False,
            "message": f"没有找到企业 ID：{company_id}"
        }

    cursor.execute("""
        INSERT INTO follow_ups (
            company_id,
            follow_up_time,
            method,
            content,
            next_follow_up_time
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        company_id,
        follow_up_time,
        method,
        content,
        next_follow_up_time
    ))

    conn.commit()

    follow_up_id = cursor.lastrowid

    conn.close()

    return {
        "success": True,
        "message": f"企业「{company[1]}」跟进记录添加成功",
        "follow_up_id": follow_up_id,
        "company_id": company_id
    }


def list_follow_ups(company_id):
    """
    查询某个企业的全部跟进记录。
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company_id,
            follow_up_time,
            method,
            content,
            next_follow_up_time
        FROM follow_ups
        WHERE company_id = ?
        ORDER BY follow_up_time DESC
    """, (company_id,))

    follow_ups = cursor.fetchall()

    conn.close()

    return follow_ups


def get_follow_up(follow_up_id):
    """
    查询单条跟进记录。
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company_id,
            follow_up_time,
            method,
            content,
            next_follow_up_time
        FROM follow_ups
        WHERE id = ?
    """, (follow_up_id,))

    follow_up = cursor.fetchone()

    conn.close()

    return follow_up


# ==================================================
# 搜索发现记录
# ==================================================


def add_search_discovery(
    company_name,
    url,
    title=None,
    source=None
):
    """
    保存搜索阶段发现的企业候选。

    即使后续官网无法访问，
    搜索发现的企业也不会丢失。
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM search_discoveries
        WHERE url = ?
        """,
        (url,)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()

        return {
            "success": False,
            "message": f"搜索发现记录已经存在：{url}",
            "discovery_id": existing[0]
        }

    cursor.execute("""
        INSERT INTO search_discoveries (
            company_name,
            url,
            title,
            source
        )
        VALUES (?, ?, ?, ?)
    """, (
        company_name,
        url,
        title,
        source
    ))

    conn.commit()

    discovery_id = cursor.lastrowid

    conn.close()

    return {
        "success": True,
        "message": f"搜索发现记录「{company_name}」保存成功",
        "discovery_id": discovery_id
    }


# ==================================================
# 程序入口
# ==================================================


if __name__ == "__main__":
    init_database()
