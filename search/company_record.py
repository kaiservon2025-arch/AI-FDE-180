from datetime import datetime


class CompanyRecord:
    """
    企业候选记录。

    与 CRM 第一版的 11 个字段保持一致。
    """

    def __init__(
        self,
        company_name="",
        contact="",
        phone="",
        email="",
        address="",
        contact_page="",
        jobs_page="",
        news="",
        source="",
        first_found_time=None,
        status="new"
    ):
        self.company_name = company_name
        self.contact = contact
        self.phone = phone
        self.email = email
        self.address = address
        self.contact_page = contact_page
        self.jobs_page = jobs_page
        self.news = news
        self.source = source
        self.first_found_time = (
            first_found_time
            if first_found_time
            else datetime.now().isoformat()
        )
        self.status = status

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "contact": self.contact,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "contact_page": self.contact_page,
            "jobs_page": self.jobs_page,
            "news": self.news,
            "source": self.source,
            "first_found_time": self.first_found_time,
            "status": self.status
        }

    def show(self):
        print("========== 企业记录 ==========")
        print(f"公司名称：{self.company_name}")
        print(f"联系人：{self.contact}")
        print(f"电话：{self.phone}")
        print(f"邮箱：{self.email}")
        print(f"地址：{self.address}")
        print(f"联系页面：{self.contact_page}")
        print(f"招聘页面：{self.jobs_page}")
        print(f"新闻：{self.news}")
        print(f"数据来源：{self.source}")
        print(f"首次发现时间：{self.first_found_time}")
        print(f"客户状态：{self.status}")
        print("==============================")
