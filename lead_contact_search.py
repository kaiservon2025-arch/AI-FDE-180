
# lead_contact_search.py
# 第1/5段

import os
import re
import requests

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from search.search_service import web_search

load_dotenv()

# ============================================================
# 常量配置
# ============================================================

THIRD_PARTY_DOMAINS = {
    "smeok.com",
    "qcc.com",
    "tianyancha.com",
    "aiqicha.baidu.com",
    "xinnet.com",
    "11467.com",
    "hc360.com",
    "made-in-china.com",
    "alibaba.com",
    "1688.com",
}

THIRD_PARTY_EMAIL_DOMAINS = {
    "qq.com",
    "163.com",
    "126.com",
    "sina.com",
    "sina.com.cn",
    "gmail.com",
    "hotmail.com",
    "outlook.com",
}

BAD_CONTACT_NAMES = {
    "联系我们",
    "联系方式",
    "联系电话",
    "公司地址",
    "客户服务",
    "服务热线",
    "售后服务",
    "业务联系",
}


# ============================================================
# 基础工具
# ============================================================

def normalize_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_company_name(company_name):
    """生成用于匹配的标准化企业名称，不用于覆盖原始名称。"""

    text = normalize_text(company_name).lower()

    suffixes = [
        "集团有限公司",
        "有限责任公司",
        "股份有限公司",
        "有限公司",
        "集团",
        "公司",
        "co., ltd.",
        "co.,ltd.",
        "limited",
        "ltd.",
    ]

    for suffix in suffixes:
        text = text.replace(suffix.lower(), "")

    text = re.sub(r"[（）()【】\[\]]", "", text)

    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", text)


def clean_company_name_for_contact_search(company_name):
    """清理常见摘要前缀和后缀，并过滤明显不是具体企业的描述。"""

    name = normalize_text(company_name)

    if not name:
        return ""

    prefixes = [
        "分别是",
        "可以联系",
        "公司简介",
        "企业简介",
        "公司名称：",
        "企业名称：",
        "公司名称:",
        "企业名称:",
        "来自东莞的",
    ]

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                changed = True

    # 清理搜索结果标题附带的官网说明
    name = re.sub(
        r"\s*[\|｜]\s*(官网|官方网站|官方网页|official website).*$",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip()

    if not name:
        return ""

    # 明确的企业类别、名单、排名或泛化描述
    invalid_phrases = [
        "东莞的台资企业",
        "世界500强企业",
        "台资企业",
        "外资企业",
        "民营企业",
        "企业名单",
        "公司排名",
        "企业排名",
        "制造企业名单",
    ]

    if any(phrase in name for phrase in invalid_phrases):
        return ""

    generic_descriptions = {
        "企业",
        "公司",
        "厂家",
        "供应商",
        "电子企业",
        "制造企业",
        "工业企业",
        "科技企业",
        "机械企业",
        "东莞的电子企业",
        "深圳的电子企业",
        "广州的电子企业",
    }

    if name in generic_descriptions:
        return ""

    # 不把明显残留的地区描述当成企业名称
    if name.startswith(("东莞的", "深圳的", "广州的")):
        return ""

    if not re.search(r"[A-Za-z\u4e00-\u9fff]", name):
        return ""

    return name


def is_valid_company_name(company_name):
    """统一的企业名称有效性判断。"""

    return bool(clean_company_name_for_contact_search(company_name))


def company_keywords(company_name):
    normalized = normalize_company_name(company_name)

    if not normalized:
        return []

    result = [normalized]

    if len(normalized) >= 4:
        result.append(normalized[:4])

    if len(normalized) >= 5:
        result.append(normalized[:5])

    return list(dict.fromkeys(result))


def get_url_host(url):
    url = normalize_text(url).lower()

    match = re.match(r"^https?://([^/:?#]+)", url)

    if not match:
        return ""

    return match.group(1).removeprefix("www.")


def is_third_party_domain(url):
    host = get_url_host(url)

    return any(
        host == domain or host.endswith("." + domain)
        for domain in THIRD_PARTY_DOMAINS
    )


# ============================================================
# Tavily 搜索
# ============================================================

def searxng_contact_search(query, max_results=3):
    """使用现有 SearXNG 搜索服务，返回兼容联系人提取流程的结果。"""
    results = web_search(query=query, limit=max_results)
    compatible_results = []

    for result in results:
        compatible_results.append({
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", result.get("description", "")),
            "raw_content": result.get("raw_content", ""),
            "source": result.get("source", "searxng"),
        })

    return compatible_results


# ============================================================
# 来源判断
# ============================================================

def detect_source_type(title, url, content=""):
    text = (
        normalize_text(title)
        + " "
        + normalize_text(url)
        + " "
        + normalize_text(content)
    ).lower()

    if is_third_party_domain(url):
        return "第三方目录"

    if any(
        word in text
        for word in ["客户案例", "建站案例", "网站建设案例"]
    ):
        return "第三方案例"

    if any(
        word in text
        for word in ["contact", "联系我们", "联系方式", "联络我们"]
    ):
        return "联系方式页面"

    if any(
        word in text
        for word in ["about us", "公司简介", "关于我们"]
    ):
        return "企业介绍"

    if any(
        word in text
        for word in ["global", "全球据点", "海外办公室"]
    ):
        return "全球据点"

    return "其他网页"

# ============================================================
# 企业匹配
# ============================================================

def verify_company_match(company_name, title, content, url):
    target = normalize_company_name(company_name)

    if not target:
        return False, "企业名称为空"

    title_norm = normalize_company_name(title)
    content_norm = normalize_company_name(content)
    url_norm = normalize_company_name(url)

    if target in title_norm:
        return True, "标题包含企业名称"

    if target in content_norm:
        return True, "内容包含企业名称"

    if target in url_norm:
        return True, "网址包含企业名称"

    for keyword in company_keywords(company_name):
        if len(keyword) >= 4:
            if keyword in title_norm:
                return True, "标题包含关键词:" + keyword

            if keyword in content_norm:
                return True, "内容包含关键词:" + keyword

    return False, "没有企业归属"


# ============================================================
# 邮箱处理
# ============================================================

def get_email_domain(email):
    email = normalize_text(email).lower()

    if "@" not in email:
        return ""

    return email.split("@")[-1]


def is_free_email(email):
    domain = get_email_domain(email)
    return domain in THIRD_PARTY_EMAIL_DOMAINS


def extract_emails(text):
    if not text:
        return []

    pattern = (
        r"[A-Za-z0-9._%+-]+"
        r"@"
        r"[A-Za-z0-9.-]+"
        r"\."
        r"[A-Za-z]{2,}"
    )

    emails = re.findall(pattern, text)

    return list(dict.fromkeys(x.lower() for x in emails))


# ============================================================
# 电话提取
# ============================================================

def extract_phones(text):
    if not text:
        return []

    patterns = [
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<!\d)(?:020|0755|0769|0760)\d{7,8}(?!\d)",
    ]

    result = []

    for pattern in patterns:
        phones = re.findall(pattern, text)

        for phone in phones:
            if phone not in result:
                result.append(phone)

    return result


# ============================================================
# 联系人提取
# ============================================================

def extract_contact_names(text):
    if not text:
        return []

    patterns = [
        r"(?:联系人|负责人|业务联系人)\s*[:：]?\s*([\u4e00-\u9fff]{2,4})",
        r"([\u4e00-\u9fff]{2,4})(?:先生|女士|小姐)",
    ]

    result = []

    for pattern in patterns:
        names = re.findall(pattern, text)

        for name in names:
            if name in BAD_CONTACT_NAMES:
                continue

            if name not in result:
                result.append(name)

    return result


# ============================================================
# 企业邮箱判断
# ============================================================

def email_matches_company_domain(email, company_name):
    domain = get_email_domain(email)

    if not domain:
        return False

    clean_domain = re.sub(r"[^a-z0-9]", "", domain.lower())

    for keyword in company_keywords(company_name):
        clean_keyword = re.sub(
            r"[^a-z0-9]",
            "",
            keyword.lower(),
        )

        if len(clean_keyword) >= 4:
            if clean_keyword in clean_domain:
                return True

    return False


# ============================================================
# 联系方式评分
# ============================================================

def contact_score(
    company_name,
    email,
    phone,
    title,
    url,
    content,
):
    score = 0

    source = detect_source_type(title, url, content)

    if source == "联系方式页面":
        score += 40
    elif source == "企业介绍":
        score += 25
    elif source == "全球据点":
        score += 5
    elif source == "第三方目录":
        score -= 40

    normalized_company = normalize_company_name(company_name)
    normalized_title = normalize_company_name(title)

    if normalized_company and normalized_company in normalized_title:
        score += 25

    if email:
        if email_matches_company_domain(email, company_name):
            score += 40
        elif is_free_email(email):
            score -= 15
        else:
            score += 10

    if phone:
        score += 15

    return score

# ============================================================
# 联系方式生成
# ============================================================

def build_contact_record(
    company_name,
    contact_name,
    email,
    phone,
    title,
    url,
    content,
    reason,
):
    score = contact_score(
        company_name,
        email,
        phone,
        title,
        url,
        content,
    )

    if score >= 65:
        status = "高可信候选"
        why = "高可信，需要人工最终确认"
    else:
        status = "待人工核实"
        why = "评分不足，需要人工确认"

    return {
        "企业名称": company_name,
        "联系人": contact_name,
        "邮箱": email,
        "电话": phone,
        "评分": score,
        "匹配依据": reason,
        "联系方式依据": why,
        "联系方式状态": status,
        "来源类型": detect_source_type(title, url, content),
        "来源": title,
        "网址": url,
        "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================
# 联系方式提取
# ============================================================

def extract_contact_candidates(
    company_name,
    title,
    content,
    url,
):
    # 防止无效名称从其他调用路径进入提取流程
    company_name = clean_company_name_for_contact_search(
        company_name
    )

    if not company_name:
        return []

    matched, reason = verify_company_match(
        company_name,
        title,
        content,
        url,
    )

    if not matched:
        return []

    text = title + "\n" + content + "\n" + url

    emails = extract_emails(text)
    phones = extract_phones(text)
    names = extract_contact_names(text)

    contact_name = names[0] if names else ""

    records = []

    for email in emails:
        records.append(
            build_contact_record(
                company_name,
                contact_name,
                email,
                "",
                title,
                url,
                content,
                reason,
            )
        )

    for phone in phones:
        records.append(
            build_contact_record(
                company_name,
                contact_name,
                "",
                phone,
                title,
                url,
                content,
                reason,
            )
        )

    return records


# ============================================================
# 去重
# ============================================================

def deduplicate_contacts(records):
    unique = {}

    for record in records:
        company = normalize_company_name(
            record.get("企业名称", "")
            or record.get("公司名称", "")
        )

        email = normalize_text(
            record.get("邮箱", "")
        ).lower()

        phone = normalize_text(
            record.get("电话", "")
        )

        if email:
            key = (company, "email", email)
        elif phone:
            key = (company, "phone", phone)
        else:
            # 纯客户资料不在此函数中保留；
            # CRM 合并函数会单独保留没有联系人的客户
            continue

        old = unique.get(key)

        if (
            old is None
            or record.get("评分", 0) > old.get("评分", 0)
        ):
            unique[key] = record

    return list(unique.values())


# ============================================================
# 排序
# ============================================================

def rank_contacts(records):
    if not records:
        return []

    return sorted(
        records,
        key=lambda item: item.get("评分", 0),
        reverse=True,
    )


# ============================================================
# 搜索关键词
# ============================================================

def build_contact_queries(company_name):
    return [
        f'"{company_name}" 联系方式',
        f'"{company_name}" 联系电话 邮箱',
        f'"{company_name}" 联系我们',
        f'"{company_name}" sales email',
        f'"{company_name}" 官网',
    ]

# ============================================================
# 单企业搜索
# ============================================================

def search_company_contacts(
    company_name,
    max_results_per_query=3,
    max_results=None,
):
    if max_results is not None:
        max_results_per_query = max_results
    # 所有调用入口统一验证企业名称
    company_name = clean_company_name_for_contact_search(
        company_name
    )

    if not company_name:
        print("跳过无效企业名称，不执行联系人搜索")
        return []

    queries = build_contact_queries(company_name)
    all_records = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        tasks = {
            executor.submit(
                searxng_contact_search,
                query,
                max_results_per_query,
            ): query
            for query in queries
        }

        for future in as_completed(tasks):
            query = tasks[future]

            try:
                search_results = future.result()
            except Exception as e:
                print("搜索失败:", query, e)
                continue

            for result in search_results:
                title = normalize_text(result.get("title", ""))
                content = normalize_text(result.get("content", ""))
                raw_content = normalize_text(
                    result.get("raw_content", "")
                )
                url = normalize_text(result.get("url", ""))

                full_content = content + "\n" + raw_content

                records = extract_contact_candidates(
                    company_name,
                    title,
                    full_content,
                    url,
                )

                all_records.extend(records)

    return rank_contacts(
        deduplicate_contacts(all_records)
    )


# ============================================================
# 批量搜索 CRM 客户
# ============================================================

def search_contacts_for_leads(
    leads,
    max_results_per_query=3,
):
    if hasattr(leads, "to_dict"):
        leads = leads.to_dict("records")

    results = []
    total = len(leads)

    for index, lead in enumerate(leads, start=1):
        original_name = (
            lead.get("企业名称")
            or lead.get("公司名称")
            or ""
        )

        company_name = clean_company_name_for_contact_search(
            original_name
        )

        if not company_name:
            print(
                f"[{index}/{total}] 跳过无效企业名称："
                f"{normalize_text(original_name)}"
            )
            continue

        print(
            f"\n[{index}/{total}] "
            f"搜索联系方式：{company_name}"
        )

        contacts = search_company_contacts(
            company_name,
            max_results_per_query,
        )

        for contact in contacts:
            item = dict(lead)
            item.update(contact)
            results.append(item)

        high_count = sum(
            1
            for contact in contacts
            if contact.get("联系方式状态") == "高可信候选"
        )

        pending_count = sum(
            1
            for contact in contacts
            if contact.get("联系方式状态") == "待人工核实"
        )

        print(
            f"候选联系方式：{len(contacts)} 条；"
            f"高可信：{high_count} 条；"
            f"待核实：{pending_count} 条"
        )

    return results


# ============================================================
# 合并客户资料
# ============================================================

def merge_contacts_to_leads(leads, contacts):
    """合并联系人和客户资料，保留所有原始客户记录。"""

    if hasattr(leads, "to_dict"):
        leads = leads.to_dict("records")

    if hasattr(contacts, "to_dict"):
        contacts = contacts.to_dict("records")

    # 仅对联系人数据去重，不对最终 CRM 客户记录做去重
    contacts = deduplicate_contacts(contacts)

    contact_map = {}

    for contact in contacts:
        contact_name = (
            contact.get("企业名称")
            or contact.get("公司名称")
            or ""
        )

        key = normalize_company_name(contact_name)

        if key:
            contact_map.setdefault(key, []).append(contact)

    result = []

    for lead in leads:
        original_name = (
            lead.get("企业名称")
            or lead.get("公司名称")
            or ""
        )

        key = normalize_company_name(original_name)
        matched_contacts = contact_map.get(key, [])

        if not matched_contacts:
            # 没有找到联系人时，仍然保留原始客户
            result.append(dict(lead))
            continue

        for contact in matched_contacts:
            item = dict(lead)
            item.update(contact)

            # 优先保留 CRM 原始企业名称，避免名称被搜索结果覆盖
            if lead.get("企业名称"):
                item["企业名称"] = lead["企业名称"]
            elif lead.get("公司名称"):
                item["公司名称"] = lead["公司名称"]

            result.append(item)

    return result

# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    company = "东莞市联诚电子科技有限公司"

    print("=" * 60)
    print("测试企业：", company)
    print(
        "搜索开始时间：",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    records = search_company_contacts(company)

    print(
        "\n搜索结束时间：",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    print("最终联系方式数量:", len(records))

    for record in records:
        print("-" * 40)
        print(record)


# ============================================================
# 文件输出工具（后续网页端使用）
# ============================================================

def save_contacts_to_excel(
    records,
    filename="contact_results.xlsx",
):
    try:
        import pandas as pd

        df = pd.DataFrame(records)
        df.to_excel(filename, index=False)

        print("已保存:", filename)

    except Exception as e:
        print("保存失败:", e)


# ============================================================
# 网页端调用接口
# ============================================================

def run_contact_search(company_name):
    cleaned_name = clean_company_name_for_contact_search(
        company_name
    )

    if not cleaned_name:
        return {
            "company": normalize_text(company_name),
            "count": 0,
            "contacts": [],
            "error": "企业名称无效，未执行搜索",
        }

    records = search_company_contacts(cleaned_name)

    return {
        "company": cleaned_name,
        "count": len(records),
        "contacts": records,
    }