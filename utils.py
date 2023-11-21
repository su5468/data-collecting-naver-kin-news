#!python

import json
from enum import Enum


class FileType(Enum):
    API_NAVER_NEWS = "api_naver_news_result"
    NEW_RESULT_RELATED = "new_result_related"


def get_news_urls(keyword: str, filetype: FileType) -> list:
    with open(f"{filetype.value}_{keyword}.txt", "rt", encoding="utf-8") as f:
        articles = json.load(f)["items"]
    ret = []
    for article in articles:
        ret.append(article["url_naver"])
    return ret
