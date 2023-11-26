#!python

import json
from os import path
from encodings.aliases import aliases
from enum import Enum
from urllib import parse
import requests


class FileType(Enum):
    NEWS = "api_naver_news_result"
    NEWS_WT = NEWS + "_with_text"
    NEWS_R = "news_result_related"
    NEWS_R_WT = NEWS_R + "_with_text"
    KIN = "api_naver_kin_result"
    KIN_WT = KIN + "_with_text"
    KIN_R = "kin_result_related"
    KIN_R_WT = KIN_R + "_with_text"

    NEWS_RL = "api_gpt_relatedness_result"
    NEWS_RL_WT = NEWS_RL + "_with_text"


def get_id_secret() -> tuple:
    with open("naver_api_key.txt", encoding="utf-8") as f:
        id, secret = map(lambda x: x.strip(), f.readlines())
    return id, secret


def get_key_org() -> tuple:
    with open("gpt_api_key.txt", encoding="utf-8") as f:
        key, org = map(lambda x: x.strip(), f.readlines())
    return key, org


def already(fname: str | list) -> bool:
    if isinstance(fname, str):
        return path.exists(fname)
    return all(path.exists(fn) for fn in fname)


def search(base_url: str, query: str, id: str, secret: str, total_pages: int) -> list:
    query = parse.quote(query)
    url = base_url + f"?query={query}&display=100"
    headers = {"X-Naver-Client-Id": id, "X-Naver-Client-Secret": secret}
    ret = []
    for page in range(total_pages):
        res = requests.get(url + f"&start={page * 100 + 1}", headers=headers, timeout=5)
        out_json = json.loads(res.text)
        for item in out_json["items"]:
            temp = {
                "title": item["title"],
                "url_naver": item["link"],
                "url_original": item["originallink"]
                if "originallink" in item
                else None,
                "description": item["description"],
                "date": item["pubDate"] if "pubDate" in item else None,
            }
            ret.append(temp)
    return ret


def write_json_on_file(fname: str, wrapped: dict) -> None:
    with open(fname, "wt", encoding="utf-8") as f:
        json.dump(wrapped, f, ensure_ascii=False, indent=4)


def get_json_from_file(fname: str) -> list:
    with open(fname, "rt", encoding="utf-8") as f:
        articles = json.load(f)["items"]
    return articles


def compare_encoding(a: str, b: str) -> bool:
    if a is None:
        return b is None
    a, b = a.lower().replace("-", "_"), b.lower().replace("-", "_")
    return aliases.get(a, a) == aliases.get(b, b)


def get_response_from_url(url: str) -> requests.models.Response:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Cookie": """NNB=RWL5HCA6VRRWK; kin_session="bXE9FAM/a9vsKxbmKxgqKxbwFxnmaqgsKAnmaqgsKAnmaqgsKAnwFAnw"; JSESSIONID=6F1D263953F1392D221F888ECFA1B6AF; nid_inf=875898310; NID_AUT=h3L76rKLNAOjgW/c2Y6/WVlV2WWvwyZFobiWiz4IYVV3ONulyEN6fM0tWXcM+ppt; NID_SES=AAABhk1mJO9hkMAQTmYE3ISmSZd1zs/536ZwMCyPP7VuCMq3o4N2GS9ZkvL5daKgoJqGPVXeuyKxOaTZvZtQd7jhdcIFJ/LFaK74iwrjpI8p2ZeTe0A4PtSyxdp3+AuhBrQa5evWtQsGau6Bbz8D4Mu66UxuQarcs0fszqwWxWoyP+RBjbIFXv1JSzDLtCJqFYxq1YmzfoJ6h7EnVmz8Ueo64+cIrWRWITaksecFN5mc/je4TwoFOYikVtWkNxiulc+M06v97aYG6lqJZS9JRkT0dCMYL7o0ERQQ6rBQ6LfG2RpYty/gmAEBv5z0YYDHmLHN+7B4off2cUM5wpDJzzQbYemlyQYIBJb1w9kTgeEoj7eC+1RAcvdjYsMCVtJ/31HBwJMbMnUa/GW6p0PEh4voBwEtDnQMqCMTgt/p/EvvtvEiWBPdy1pEy2GPicx75mAEPr32L4aGf+j+Fce5hOINurbzK131zt4hu1CknclO2J9ixY9fPbPyogM8+oZfpWCQoZ7sjtiFo+yd0XxDCrY+ero=; NID_JKL=S/JCbq2t+16ccKoeou0HBf/l7bybFrpgUqLZSgse3t0=""",
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
    ):
        return None
    return res
