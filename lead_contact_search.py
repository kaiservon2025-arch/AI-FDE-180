import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"


# ============================================================
# 基础工具
# ============================================================

def normalize_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_list(value):
    if value is None:
        return []

    if isinstance(value, str):
        parts = re.split(r"[,，、;\n]+", value)
        return [normalize_text(x) for x in parts if normalize_text(x)]

    return [normalize_text(x) for x in value if normalize_text(x)]


def normalize_company_name(company_name):
    text = normalize_text(company_name).lower()

    text = re.sub(r"（.*?）", "", text)
    text = re.sub(r"\(.*?\)", "", text)

    suffixes = [
        "集团有限公司",
        "有限责任公司",
        "股份有限公司",
        "有限公司",
        "集团",
        "公司",
        "co.,ltd.",
        "co., ltd.",
        "limited",
        "ltd.",
        "ltd",
    ]

    for suffix in suffixes:
        text = text.replace(suffix.lower(), "")

    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", text)

    return text


def company_keywords(company_name):
    normalized = normalize_company_name(company_name)

    if not normalized:
        return []

    keywords = [normalized]

    if len(normalized) >= 4:
        keywords.append(normalized[:4])

    if len(normalized) >= 5:
        keywords.append(normalized[:5])

    return list(dict.fromkeys(keywords))


# ============================================================
# Tavily
# ============================================================

def tavily_search(query, max_results=8):

    if not TAVILY_API_KEY:
        raise RuntimeError(
            "没有找到 TAVILY_API_KEY，请检查 .env 文件。"
        )

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": True,
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    return data.get("results", [])


# ============================================================
# 来源类型
# ============================================================

def detect_source_type(title, url, content=""):

    text = f"{title} {url} {content}".lower()

    if "招聘" in text or "job" in text or "career" in text:
        return "招聘网站"

    if "linkedin" in text or "脉脉" in text:
        return "职业社交"

    if "微信" in text or "weixin" in text or "公众号" in text:
        return "微信公众号"

    if "招标" in text or "采购" in text or "bid" in text:
        return "招投标/采购"

    if "展会" in text or "conference" in text or "expo" in text:
        return "展会/会议"

    if (
        "政府" in text
        or "gov.cn" in text
        or "协会" in text
        or "产业园" in text
    ):
        return "政府/协会/产业园"

    if url.lower().endswith(".pdf") or ".pdf?" in url.lower():
        return "PDF/公开资料"

    if any(
        x in text
        for x in [
            "新闻",
            "news",
            "媒体",
            "新浪",
            "网易",
            "腾讯",
            "搜狐",
        ]
    ):
        return "新闻/媒体"

    if (
        "官网" in text
        or "联系我们" in text
        or "contact" in text.lower()
    ):
        return "企业官网"

    return "其他公开网页"


# ============================================================
# 企业归属验证
# ============================================================

def verify_company_match(
    company_name,
    title,
    content,
    url
):

    target = normalize_company_name(company_name)

    if not target:
        return False, "目标企业名称为空"

    title_norm = normalize_company_name(title)
    content_norm = normalize_company_name(content)
    url_norm = normalize_company_name(url)

    if target in title_norm:
        return True, "页面标题明确出现目标企业"

    if target in content_norm:
        return True, "页面内容明确出现目标企业"

    if target in url_norm:
        return True, "网址中明确出现目标企业"

    keywords = company_keywords(company_name)

    for keyword in keywords:

        if len(keyword) < 4:
            continue

        if keyword in title_norm:
            return True, f"页面标题出现企业核心名称：{keyword}"

        if keyword in content_norm:
            return True, f"页面内容出现企业核心名称：{keyword}"

        if keyword in url_norm:
            return True, f"网址出现企业核心名称：{keyword}"

    return False, "页面没有发现目标企业的明确归属证据"


# ============================================================
# 第三方联系方式排除
# ============================================================

THIRD_PARTY_EMAIL_DOMAINS = {
    "tianyancha.com",
    "xinnet.com",
    "qcc.com",
    "baidu.com",
    "sina.com.cn",
    "sohu.com",
    "qq.com",
    "163.com",
    "126.com",
    "aliyun.com",
    "alibaba-inc.com",
    "tencent.com",
    "microsoft.com",
    "google.com",
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "linkedin.com",
}


def get_email_domain(email):

    email = normalize_text(email).lower()

    if "@" not in email:
        return ""

    return email.split("@", 1)[1]


def is_third_party_email(email):

    domain = get_email_domain(email)

    if not domain:
        return False

    if domain in THIRD_PARTY_EMAIL_DOMAINS:
        return True

    return False


def email_matches_company_domain(
    email,
    company_name,
    url
):

    domain = get_email_domain(email)

    if not domain:
        return False

    company_words = company_keywords(company_name)

    clean_domain = re.sub(
        r"[^a-z0-9]",
        "",
        domain.lower()
    )

    for word in company_words:

        clean_word = re.sub(
            r"[^a-z0-9]",
            "",
            word.lower()
        )

        if (
            clean_word
            and len(clean_word) >= 4
            and clean_word in clean_domain
        ):
            return True

    # URL 域名匹配
    url_match = re.search(
        r"https?://(?:www\.)?([^/]+)",
        url.lower()
    )

    if url_match:

        site_domain = re.sub(
            r"[^a-z0-9]",
            "",
            url_match.group(1)
        )

        if (
            clean_domain
            and site_domain
            and (
                clean_domain in site_domain
                or site_domain in clean_domain
            )
        ):
            return True

    return False


# ============================================================
# 邮箱
# ============================================================

def extract_emails(text):

    if not text:
        return []

    pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    emails = re.findall(
        pattern,
        text
    )

    result = []

    for email in emails:

        email = email.strip().lower()

        if any(
            x in email
            for x in [
                "example.com",
                "example.cn",
                "test.com",
            ]
        ):
            continue

        if email not in result:
            result.append(email)

    return result


# ============================================================
# 电话
# ============================================================

def extract_phones(text):

    if not text:
        return []

    result = []

    mobile_pattern = (
        r"(?<!\d)1[3-9]\d{9}(?!\d)"
    )

    mobiles = re.findall(
        mobile_pattern,
        text
    )

    for phone in mobiles:

        if phone not in result:
            result.append(phone)

    landline_pattern = (
        r"(?<!\d)"
        r"(?:020|0660|0662|0663|0751|0752|0753|0754|0755|0756|"
        r"0757|0758|0759|0760|0762|0763|0766|0768|0769)"
        r"\d{7,8}"
        r"(?!\d)"
    )

    landlines = re.findall(
        landline_pattern,
        text
    )

    for phone in landlines:

        if phone not in result:
            result.append(phone)

    return result


# ============================================================
# 联系人
# ============================================================

def extract_contact_names(text):

    if not text:
        return []

    result = []

    patterns = [

        # 联系人：洪先生
        r"(?:联系人|联络人|负责人)"
        r"\s*[:：]\s*"
        r"([\u4e00-\u9fff]{2,4})"
        r"(?:先生|女士|小姐)?",

        # 洪先生 / 洪女士
        r"([\u4e00-\u9fff]{2,4})"
        r"(?:先生|女士|小姐)",

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for name in matches:

            name = normalize_text(name)

            # ------------------------------------------------
            # 排除明显不是人名的词
            # ------------------------------------------------

            invalid_names = {
                "联络方式",
                "联系方式",
                "联系方法",
                "联系我们",
                "联系电话",
                "联络我们",
                "客户服务",
                "客服中心",
                "服务热线",
                "销售团队",
                "公司地址",
                "电子邮箱",
            }

            if name in invalid_names:
                continue

            if name.endswith(
                (
                    "方式",
                    "方法",
                    "电话",
                    "邮箱",
                    "地址",
                    "我们",
                )
            ):
                continue

            if (
                len(name) >= 2
                and name not in result
            ):
                result.append(name)

    return result


# ============================================================
# 职位
# ============================================================

def extract_job_titles(text):

    if not text:
        return []

    titles = [
        "董事长",
        "总经理",
        "副总经理",
        "总裁",
        "副总裁",
        "CEO",
        "CFO",
        "CTO",
        "COO",
        "HR总监",
        "人力资源总监",
        "人事总监",
        "人力资源经理",
        "人事经理",
        "行政经理",
        "招聘经理",
        "招聘负责人",
        "HR经理",
        "HRBP",
        "人力资源负责人",
        "销售总监",
        "销售经理",
        "市场总监",
        "市场经理",
        "采购经理",
        "招商主管",
        "总监",
        "经理",
    ]

    result = []

    for title in titles:

        if title.lower() in text.lower():

            if title not in result:
                result.append(title)

    return result


# ============================================================
# 信息日期
# ============================================================

def extract_information_date(text):

    if not text:
        return ""

    patterns = [
        r"(20\d{2}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
        r"(20\d{2}[./-]\d{1,2}[./-]\d{1,2})",
        r"(20\d{2}年\d{1,2}月)",
        r"(20\d{2}年)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(1)

    return ""


# ============================================================
# 判断联系方式是否属于目标企业
# ============================================================

def verify_contact_ownership(
    company_name,
    email,
    phone,
    title,
    content,
    url
):

    # --------------------------------------------------------
    # 邮箱判断
    # --------------------------------------------------------

    if email:

        if is_third_party_email(email):

            return (
                False,
                "第三方平台/公共邮箱，不作为企业联系方式"
            )

        if email_matches_company_domain(
            email,
            company_name,
            url
        ):

            return (
                True,
                "邮箱域名与目标企业/官网域名存在关联"
            )

        # 企业官网页面明确出现邮箱
        if (
            normalize_company_name(company_name)
            in normalize_company_name(content)
            and email.lower() in content.lower()
        ):

            return (
                True,
                "企业页面明确展示该邮箱"
            )

        # 企业官网页面
        source_type = detect_source_type(
            title,
            url,
            content
        )

        if source_type == "企业官网":

            return (
                True,
                "企业官网页面公开展示该邮箱"
            )

        # 普通邮箱但没有企业域名证据
        return (
            True,
            "目标企业公开页面中出现该邮箱，暂未发现第三方平台归属"
        )

    # --------------------------------------------------------
    # 电话判断
    # --------------------------------------------------------

    if phone:

        if (
            normalize_company_name(company_name)
            in normalize_company_name(content)
        ):

            return (
                True,
                "企业公开页面明确展示该电话"
            )

        return (
            True,
            "目标企业公开搜索结果中出现该电话"
        )

    return (
        False,
        "没有有效联系方式"
    )


# ============================================================
# 联系方式候选提取
# ============================================================

def extract_contact_candidates(
    company_name,
    title,
    content,
    url
):

    title = normalize_text(title)
    content = normalize_text(content)
    url = normalize_text(url)

    matched, company_reason = verify_company_match(
        company_name,
        title,
        content,
        url
    )

    if not matched:
        return []

    combined_text = (
        f"{title}\n{content}"
    )

    emails = extract_emails(
        combined_text
    )

    phones = extract_phones(
        combined_text
    )

    names = extract_contact_names(
        combined_text
    )

    job_titles = extract_job_titles(
        combined_text
    )

    information_date = extract_information_date(
        combined_text
    )

    source_type = detect_source_type(
        title,
        url,
        content
    )

    candidates = []

    # --------------------------------------------------------
    # 联系人只取真正识别出的名字
    # --------------------------------------------------------

    contact_name = ""

    if names:
        contact_name = names[0]

    # --------------------------------------------------------
    # 不再默认把职位绑定到所有联系方式
    #
    # 只有页面同时存在明确联系人时，才暂时绑定职位。
    # --------------------------------------------------------

    job_title = ""

    if contact_name and job_titles:
        job_title = job_titles[0]

    # --------------------------------------------------------
    # 邮箱
    # --------------------------------------------------------

    for email in emails:

        owned, ownership_reason = verify_contact_ownership(
            company_name=company_name,
            email=email,
            phone="",
            title=title,
            content=content,
            url=url
        )

        if not owned:
            continue

        candidates.append({
            "企业名称": company_name,
            "联系人": contact_name,
            "职位": job_title,
            "邮箱": email,
            "电话": "",
            "企业匹配状态": "已确认",
            "联系方式状态": "已确认",
            "联系方式归属依据": ownership_reason,
            "匹配依据": company_reason,
            "来源类型": source_type,
            "来源": title,
            "网址": url,
            "信息日期": information_date,
            "抓取时间": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        })

    # --------------------------------------------------------
    # 电话
    # --------------------------------------------------------

    for phone in phones:

        owned, ownership_reason = verify_contact_ownership(
            company_name=company_name,
            email="",
            phone=phone,
            title=title,
            content=content,
            url=url
        )

        if not owned:
            continue

        candidates.append({
            "企业名称": company_name,
            "联系人": contact_name,
            "职位": job_title,
            "邮箱": "",
            "电话": phone,
            "企业匹配状态": "已确认",
            "联系方式状态": "已确认",
            "联系方式归属依据": ownership_reason,
            "匹配依据": company_reason,
            "来源类型": source_type,
            "来源": title,
            "网址": url,
            "信息日期": information_date,
            "抓取时间": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        })

    return candidates


# ============================================================
# 联系方式去重
# ============================================================

def deduplicate_contacts(records):

    unique = {}

    for record in records:

        company = normalize_text(
            record.get("企业名称", "")
        )

        email = normalize_text(
            record.get("邮箱", "")
        ).lower()

        phone = normalize_text(
            record.get("电话", "")
        )

        contact = normalize_text(
            record.get("联系人", "")
        )

        if email:

            key = (
                normalize_company_name(company),
                "email",
                email,
            )

        elif phone:

            key = (
                normalize_company_name(company),
                "phone",
                phone,
            )

        else:

            key = (
                normalize_company_name(company),
                "other",
                contact,
            )

        if key not in unique:

            unique[key] = record

        else:

            old = unique[key]

            for field in [
                "联系人",
                "职位",
                "信息日期",
                "来源类型",
                "来源",
                "网址",
                "匹配依据",
                "联系方式归属依据",
            ]:

                if (
                    not old.get(field)
                    and record.get(field)
                ):
                    old[field] = record[field]

    return list(unique.values())


# ============================================================
# 搜索关键词
# ============================================================

def build_contact_queries(company_name):

    return [
        f'"{company_name}" 联系方式 电话 邮箱',
        f'"{company_name}" 联系人 手机',
        f'"{company_name}" 总经理 联系方式',
        f'"{company_name}" 人事 HR 联系方式',
        f'"{company_name}" 招聘 联系人',
        f'"{company_name}" 官网 联系我们',
        f'"{company_name}" 新闻 联系方式',
        f'"{company_name}" 招投标 联系人',
        f'"{company_name}" 展会 联系人',
    ]


# ============================================================
# 单企业联系方式搜索
# ============================================================

def search_company_contacts(
    company_name,
    max_results_per_query=5
):

    all_records = []

    queries = build_contact_queries(
        company_name
    )

    for query in queries:

        try:

            results = tavily_search(
                query,
                max_results=max_results_per_query
            )

        except Exception as e:

            print(
                f"搜索失败：{query}"
            )

            print(
                f"错误：{e}"
            )

            continue

        for result in results:

            title = normalize_text(
                result.get("title", "")
            )

            content = normalize_text(
                result.get("content", "")
            )

            raw_content = normalize_text(
                result.get("raw_content", "")
            )

            url = normalize_text(
                result.get("url", "")
            )

            if raw_content:

                full_content = (
                    f"{content}\n{raw_content}"
                )

            else:

                full_content = content

            candidates = extract_contact_candidates(
                company_name=company_name,
                title=title,
                content=full_content,
                url=url,
            )

            all_records.extend(
                candidates
            )

    return deduplicate_contacts(
        all_records
    )


# ============================================================
# 批量搜索
# ============================================================

def search_contacts_for_leads(
    leads,
    max_results_per_query=5
):

    results = []

    if hasattr(leads, "to_dict"):
        leads = leads.to_dict(
            "records"
        )

    for index, lead in enumerate(
        leads,
        start=1
    ):

        company_name = normalize_text(
            lead.get("企业名称")
            or lead.get("company")
            or lead.get("公司名称")
            or ""
        )

        if not company_name:
            continue

        print(
            f"\n[{index}/{len(leads)}]"
            f" 正在搜索联系方式："
            f"{company_name}"
        )

        contacts = search_company_contacts(
            company_name,
            max_results_per_query=
                max_results_per_query
        )

        for contact in contacts:

            merged = dict(lead)

            merged.update(contact)

            results.append(
                merged
            )

        print(
            f"找到已确认联系方式："
            f"{len(contacts)} 条"
        )

    return results


# ============================================================
# 合并联系方式
# ============================================================

def merge_contacts_to_leads(
    leads,
    contacts
):

    if hasattr(leads, "to_dict"):
        leads = leads.to_dict(
            "records"
        )

    if hasattr(contacts, "to_dict"):
        contacts = contacts.to_dict(
            "records"
        )

    contact_map = {}

    for contact in contacts:

        company = normalize_company_name(
            contact.get(
                "企业名称",
                ""
            )
        )

        if not company:
            continue

        contact_map.setdefault(
            company,
            []
        ).append(contact)

    final_records = []

    for lead in leads:

        company_name = normalize_text(
            lead.get("企业名称")
            or lead.get("company")
            or lead.get("公司名称")
            or ""
        )

        normalized_company = normalize_company_name(
            company_name
        )

        matched_contacts = contact_map.get(
            normalized_company,
            []
        )

        if not matched_contacts:
            continue

        for contact in matched_contacts:

            merged = dict(lead)

            merged.update(contact)

            final_records.append(
                merged
            )

    return deduplicate_contacts(
        final_records
    )


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":

    test_company = (
        "东莞市联诚电子科技有限公司"
    )

    print("=" * 60)
    print("联系方式搜索测试")
    print("=" * 60)

    print()
    print(
        f"企业：{test_company}"
    )

    records = search_company_contacts(
        test_company,
        max_results_per_query=5
    )

    print(
        f"找到已确认联系方式："
        f"{len(records)} 条"
    )

    print("-" * 60)

    for record in records:

        print(
            f"联系人："
            f"{record.get('联系人', '')}"
        )

        print(
            f"职位："
            f"{record.get('职位', '')}"
        )

        print(
            f"邮箱："
            f"{record.get('邮箱', '')}"
        )

        print(
            f"电话："
            f"{record.get('电话', '')}"
        )

        print(
            f"企业匹配："
            f"{record.get('企业匹配状态', '')}"
        )

        print(
            f"联系方式状态："
            f"{record.get('联系方式状态', '')}"
        )

        print(
            f"联系方式归属依据："
            f"{record.get('联系方式归属依据', '')}"
        )

        print(
            f"匹配依据："
            f"{record.get('匹配依据', '')}"
        )

        print(
            f"来源类型："
            f"{record.get('来源类型', '')}"
        )

        print(
            f"来源："
            f"{record.get('来源', '')}"
        )

        print(
            f"网址："
            f"{record.get('网址', '')}"
        )

        print(
            f"信息日期："
            f"{record.get('信息日期', '')}"
        )

        print("-" * 60)

    print()
    print("测试完成")