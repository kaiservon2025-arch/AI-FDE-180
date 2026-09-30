class SearchConfig:
    def __init__(
        self,
        keyword="",
        country="",
        industry="",
        city="",
        company_size=""
    ):
        self.keyword = keyword
        self.country = country
        self.industry = industry
        self.city = city
        self.company_size = company_size

    def show(self):
        print("========== 搜索条件 ==========")
        print(f"关键词：{self.keyword}")
        print(f"国家：{self.country}")
        print(f"行业：{self.industry}")
        print(f"城市：{self.city}")
        print(f"企业规模：{self.company_size}")
        print("==============================")