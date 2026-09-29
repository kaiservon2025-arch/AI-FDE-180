import os

import requests

from dotenv import load_dotenv


load_dotenv()


FACTORY_API_KEY = os.getenv(
    "FACTORY_API_KEY"
)


def search_factory_companies(
    keyword="",
    province="",
    city="",
    industry="",
    limit=20
):
    """
    搜索中国制造企业。

    当前版本：
    先建立API调用结构。
    """

    if not FACTORY_API_KEY:
        raise ValueError(
            "没有找到 FACTORY_API_KEY，"
            "请先在 .env 中配置API Key。"
        )


    # ==========================================
    # 真实API地址将在这里配置
    # ==========================================

    api_url = "这里填写真实API地址"


    params = {
        "keyword": keyword,
        "province": province,
        "city": city,
        "industry": industry,
        "limit": limit
    }


    headers = {
        "Authorization": (
            f"Bearer {FACTORY_API_KEY}"
        )
    }


    response = requests.get(
        api_url,
        params=params,
        headers=headers,
        timeout=30
    )


    response.raise_for_status()


    return response.json()