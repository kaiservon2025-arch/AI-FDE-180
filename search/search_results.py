class SearchResult:
    def __init__(
        self,
        title="",
        url="",
        description="",
        source=""
    ):
        self.title = title
        self.url = url
        self.description = description
        self.source = source

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "source": self.source
        }

    def show(self):
        print("========== 搜索结果 ==========")
        print(f"标题：{self.title}")
        print(f"网址：{self.url}")
        print(f"描述：{self.description}")
        print(f"来源：{self.source}")
        print("==============================")