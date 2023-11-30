#!python
# feel free to use this.
# if you have any question, contact me.
# 조건희( su5468@korea.ac.kr )

from typing import List, Dict, Tuple, Optional
import json
from os import path
from encodings.aliases import aliases
from enum import Enum
from urllib import parse
import requests


class FileType(Enum):
    """
    수집한 데이터 파일의 종류를 지정하는 Enum 타입
    데이터 수집 결과는 반드시 아래 타입 중 하나임
    파일명은 f"{filetype.value}_{keyword}.txt" 형식임
    """

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


def get_id_secret() -> Tuple[str, str]:
    """
    naver_api_key.txt의 첫째 줄과 둘째 줄에서 ID와 SECRET을 읽어들이는 함수

    Returns:
        Tuple[str, str]: naver api를 위한 id, secret의 튜플
    """
    with open("naver_api_key.txt", encoding="utf-8") as f:
        id, secret = map(lambda x: x.strip(), f.readlines())
    return id, secret


def get_key_org() -> Tuple[str, str]:
    """
    gpt_api_key.txt의 첫째 줄과 둘째 줄에서 KEY와 ORGANIZATION을 읽어들이는 함수

    Returns:
        Tuple[str, str]: openai api를 위한 key, organization의 튜플
    """
    with open("gpt_api_key.txt", encoding="utf-8") as f:
        key, org = map(lambda x: x.strip(), f.readlines())
    return key, org


def already(fname: str | List[str]) -> bool:
    """
    fname이 문자열이면, 현재 폴더에 파일명이 fname인 파일이 있는지 확인한다
    fname이 리스트이면, 현재 폴더에서 fname 안의 모든 원소에 대해 확인한다

    Args:
        fname (str | list): 파일명 문자열(확장자 포함) 또는 파일명 문자열의 리스트

    Returns:
        bool: 해당 파일들이 모두 이미 존재하는지의 여부
    """
    if isinstance(fname, str):
        return path.exists(fname)
    return all(path.exists(fn) for fn in fname)


def search(
    base_url: str, query: str, id: str, secret: str, total_pages: int
) -> List[Dict[str, Optional[str]]]:
    """
    네이버 검색 api용 함수로, api 결과를 json으로 받을 것을 가정함
    현재 네이버 뉴스 및 지식IN과 compatible

    Args:
        base_url (str): api 기본 url
        query (str): 검색할 키워드
        id (str): naver api id
        secret (str): naver api secret
        total_pages (int): 한 페이지에 100개 결과가 있을 때, 총 페이지 수(최대 10 페이지 = 1000개)

    Returns:
        List[Dict[str, Optional[str]]]: [{아티클 0 정보}, {아티클 1 정보}, ...]
            ["title"]: 아티클의 제목(검색 키워드는 <b> 태그로 둘러쌓임)
            ["url_naver"]: 아티클의 주소, 뉴스인 경우 네이버 뉴스 주소(없으면 원본 기사 주소)
            ["url_original"]: 뉴스인 경우 원본 기사 주소, 지식IN이면 None
            ["description"]: 아티클 본문에서 키워드가 등장한 부분의 패시지
            ["date"]: 뉴스인 경우 뉴스의 날짜, 지식IN이면 None
    """
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


def write_json_on_file(fname: str, wrapped: dict | list) -> None:
    """
    파일명이 fname인 파일을 만들어 wrapped를 json 형식으로 저장

    Args:
        fname (str): 파일명 문자열(확장자 포함)
        wrapped (dict | list): json으로 덤프될 수 있는 딕셔너리, 리스트
    """
    with open(fname, "wt", encoding="utf-8") as f:
        json.dump(wrapped, f, ensure_ascii=False, indent=4)


def get_json_from_file(fname: str) -> dict | list:
    """
    fname인 json 파일을 읽거

    Args:
        fname (str): 파일명 문자열(확장자 포함)

    Returns:
        dict | list: json 파일의 내용물을 파이썬 객체로 변환한 결과
    """
    with open(fname, "rt", encoding="utf-8") as f:
        articles = json.load(f)["items"]
    return articles


def compare_encoding(a: Optional[str], b: Optional[str]) -> bool:
    """
    두 인코딩 문자열이 같은 인코딩을 지시하는지의 여부


    Args:
        a (Optional[str]): 첫 번째 인코딩 문자열
        b (Optional[str]): 두 번째 인코딩 문자열

    Returns:
        bool: 둘 다 None이면 True, 그 외의 경우 같은 인코딩 문자열이어야 True

    Usage:
        compare_encoding("utf-8", "utf8") -> True
        compare_encoding("cp949", "utf8") -> False
    """

    if a is None:
        return b is None
    a, b = a.lower().replace("-", "_"), b.lower().replace("-", "_")
    return aliases.get(a, a) == aliases.get(b, b)


def get_response_from_url(url: str) -> Optional[requests.models.Response]:
    """
    requests 모듈을 이용해 url에 get 요청을 보냄
    User-Agent 헤더를 설정하고 올바른 요청을 받지 못하는 경우 None을 반환함
    TODO: 지식인 쿠키 설정

    Args:
        url (str): get 요청을 보낼 url

    Returns:
        Optional[requests.models.Response]: 응답 결과인 requests 모듈의 response 객체거나, 올바르지 않은 결과인 경우 None
    """
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
