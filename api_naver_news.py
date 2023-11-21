#!python

import requests
import json
from urllib import parse


def search(query: str, id: str, secret: str, total_pages: int) -> list:
    query = parse.quote(query)
    url = (
        "https://openapi.naver.com/v1/search/news.json" + f"?query={query}&display=100"
    )
    headers = {"X-Naver-Client-Id": id, "X-Naver-Client-Secret": secret}
    ret = []
    for page in range(total_pages):
        res = requests.get(url + f"&start={page * 100 + 1}", headers=headers, timeout=5)
        out_json = json.loads(res.text)
        for item in out_json["items"]:
            temp = {
                "title": item["title"],
                "url_naver": item["link"],
                "url_original": item["originallink"],
                "description": item["description"],
                "date": item["pubDate"],
            }
            ret.append(temp)
    return ret


def main():
    keyword = "환자-의사 공유 의사결정"
    num_of_pages = 10

    with open("naver_api_key.txt", encoding="utf-8") as f:
        ID, SECRET = map(lambda x: x.strip(), f.readlines())

    search_result = search(keyword, ID, SECRET, num_of_pages)

    with open(f"api_naver_news_result_{keyword}.txt", "wt", encoding="utf-8") as f:
        wrapped = {"keyword": keyword, "items": search_result}
        json.dump(wrapped, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
