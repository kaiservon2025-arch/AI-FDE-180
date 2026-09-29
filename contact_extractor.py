import re
import pandas as pd
from urllib.parse import urlparse


GUANGDONG_AREA_CODES = {
    "020",
    "0660",
    "0662",
    "0663",
    "0751",
    "0752",
    "0753",
    "0754",
    "0755",
    "0756",
    "0757",
    "0758",
    "0759",
    "0760",
    "0762",
    "0763",
    "0766",
    "0768",
    "0769"
}


def extract_emails(text):

    if not text:
        return []

    pattern = r"""
        [A-Za-z0-9._%+-]+
        @
        [A-Za-z0-9.-]+\.[A-Za-z]{2,}
    """

    matches = re.findall(
        pattern,
        text,
        re.VERBOSE
    )

    emails = []

    for email in matches:

        email = email.strip().lower()

        if email not in emails:
            emails.append(email)

    return emails


def normalize_email(email):

    if not email:
        return ""

    email = str(email).strip().lower()

    email = re.sub(
        r"\s+",
        "",
        email
    )

    return email


def normalize_phone(phone):

    if not phone:
        return ""

    phone = str(phone).strip()

    phone = (
        phone
        .replace("－", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace(" ", "")
        .replace("\t", "")
        .replace("(", "")
        .replace(")", "")
    )

    phone = phone.replace(
        "-",
        ""
    )

    return phone


def extract_phones(text):

    if not text:
        return []

    phones = []

    mobile_pattern = (
        r"(?<!\d)"
        r"1[3-9]\d{9}"
        r"(?!\d)"
    )

    mobile_matches = re.findall(
        mobile_pattern,
        text
    )

    for phone in mobile_matches:

        phone = normalize_phone(
            phone
        )

        if phone not in phones:
            phones.append(phone)

    landline_pattern = (
        r"(?<!\d)"
        r"(0\d{2,3})"
        r"[-－\s]?"
        r"(\d{7,8})"
        r"(?!\d)"
    )

    landline_matches = re.findall(
        landline_pattern,
        text
    )

    for area_code, number in landline_matches:

        if area_code not in GUANGDONG_AREA_CODES:
            continue

        phone = (
            area_code
            + number
        )

        phone = normalize_phone(
            phone
        )

        if phone not in phones:
            phones.append(phone)

    return phones


def extract_contacts(text):

    if not text:
        return []

    patterns = [
        r"联系人[：:\s]+([一-龥]{2,4})",
        r"联络人[：:\s]+([一-龥]{2,4})",
        r"负责人[：:\s]+([一-龥]{2,4})",
        r"联系人姓名[：:\s]+([一-龥]{2,4})",
        r"销售联系人[：:\s]+([一-龥]{2,4})",
        r"业务联系人[：:\s]+([一-龥]{2,4})"
    ]

    contacts = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for name in matches:

            name = name.strip()

            if name not in contacts:
                contacts.append(name)

    return contacts


def extract_job_titles(text):

    if not text:
        return []

    titles = [
        "人事经理",
        "人力资源经理",
        "人事主管",
        "人力资源主管",
        "HR经理",
        "HR主管",
        "招聘经理",
        "招聘主管",
        "行政经理",
        "行政主管",
        "总经理",
        "副总经理",
        "董事长",
        "总监",
        "经理",
        "主管"
    ]

    found = []

    for title in titles:

        if title in text:

            if title not in found:
                found.append(title)

    return found


def extract_domain(url):

    if not url:
        return ""

    try:

        parsed = urlparse(url)

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:

        return ""


def extract_contact_from_page(row):

    title = str(
        row.get(
            "标题",
            ""
        )
    )

    summary = str(
        row.get(
            "网页内容",
            ""
        )
    )

    page_text = str(
        row.get(
            "网页正文",
            ""
        )
    )

    url = str(
        row.get(
            "网址",
            ""
        )
    )

    information_date = row.get(
        "信息日期",
        ""
    )

    company = row.get(
        "公司",
        ""
    )

    full_text = (
        title
        + "\n"
        + summary
        + "\n"
        + page_text
    )

    emails = extract_emails(
        full_text
    )

    phones = extract_phones(
        full_text
    )

    contacts = extract_contacts(
        full_text
    )

    job_titles = extract_job_titles(
        full_text
    )

    domain = extract_domain(
        url
    )

    records = []

    max_length = max(
        len(emails),
        len(phones),
        1
    )

    for i in range(max_length):

        email = (
            emails[i]
            if i < len(emails)
            else ""
        )

        phone = (
            phones[i]
            if i < len(phones)
            else ""
        )

        records.append(
            {
                "公司": company,
                "邮箱": normalize_email(
                    email
                ),
                "电话": normalize_phone(
                    phone
                ),
                "联系人": "、".join(
                    contacts
                ),
                "职位": "、".join(
                    job_titles
                ),
                "官网域名": domain,
                "信息日期": information_date,
                "来源": row.get(
                    "来源",
                    ""
                ),
                "来源网址": url,
                "网页标题": row.get(
                    "网页标题",
                    title
                ),
                "网页抓取成功": row.get(
                    "网页抓取成功",
                    False
                )
            }
        )

    return records


def deduplicate_contacts(
    contacts_df
):

    if contacts_df is None:
        return pd.DataFrame()

    if len(contacts_df) == 0:
        return contacts_df

    df = contacts_df.copy()

    df["邮箱"] = (
        df["邮箱"]
        .fillna("")
        .astype(str)
        .apply(
            normalize_email
        )
    )

    df["电话"] = (
        df["电话"]
        .fillna("")
        .astype(str)
        .apply(
            normalize_phone
        )
    )

    df["公司"] = (
        df["公司"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    original_count = len(df)

    keep_indexes = []

    seen_company_email = set()
    seen_company_phone = set()

    for index, row in df.iterrows():

        company = row["公司"]

        email = row["邮箱"]

        phone = row["电话"]

        email_key = None
        phone_key = None

        if email:
            email_key = (
                company.lower(),
                email
            )

        if phone:
            phone_key = (
                company.lower(),
                phone
            )

        duplicate = False

        if (
            email_key
            and email_key in seen_company_email
        ):
            duplicate = True

        if (
            phone_key
            and phone_key in seen_company_phone
        ):
            duplicate = True

        if duplicate:
            continue

        keep_indexes.append(
            index
        )

        if email_key:
            seen_company_email.add(
                email_key
            )

        if phone_key:
            seen_company_phone.add(
                phone_key
            )

    result_df = df.loc[
        keep_indexes
    ].reset_index(
        drop=True
    )

    removed_count = (
        original_count
        - len(result_df)
    )

    print()
    print(
        "联系方式去重完成"
    )

    print(
        f"去重前：{original_count}"
    )

    print(
        f"去重后：{len(result_df)}"
    )

    print(
        f"删除重复：{removed_count}"
    )

    return result_df


def extract_contacts_from_pages(
    pages_df
):

    if pages_df is None:

        raise ValueError(
            "网页数据为空。"
        )

    if len(pages_df) == 0:

        return pd.DataFrame()

    all_records = []

    total = len(pages_df)

    print()
    print("================================")
    print("开始提取联系方式")
    print("================================")
    print()

    for index, row in pages_df.iterrows():

        title = row.get(
            "标题",
            ""
        )

        print(
            f"[{index + 1}/{total}] "
            f"{title}"
        )

        try:

            records = (
                extract_contact_from_page(
                    row
                )
            )

            all_records.extend(
                records
            )

            email_count = sum(
                1
                for record in records
                if record["邮箱"]
            )

            phone_count = sum(
                1
                for record in records
                if record["电话"]
            )

            print(
                f"  → 邮箱："
                f"{email_count} "
                f"电话："
                f"{phone_count}"
            )

        except Exception as e:

            print(
                f"  → 提取失败：{e}"
            )

    result_df = pd.DataFrame(
        all_records
    )

    print()
    print("================================")
    print("联系方式提取完成")
    print("================================")
    print()

    print(
        f"网页数量："
        f"{len(pages_df)}"
    )

    print(
        f"原始联系方式记录："
        f"{len(result_df)}"
    )

    if len(result_df) > 0:

        email_count = (
            result_df[
                "邮箱"
            ]
            .astype(str)
            .str.strip()
            .ne("")
            .sum()
        )

        phone_count = (
            result_df[
                "电话"
            ]
            .astype(str)
            .str.strip()
            .ne("")
            .sum()
        )

        print(
            f"邮箱："
            f"{email_count}"
        )

        print(
            f"电话："
            f"{phone_count}"
        )

    result_df = deduplicate_contacts(
        result_df
    )

    return result_df