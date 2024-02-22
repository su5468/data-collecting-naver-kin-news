#!python

from typing import List, Dict, Tuple, Optional
import re
import time
import json
import datetime as dt
from os import path
from encodings.aliases import aliases
from configparser import ConfigParser
from enum import Enum
from urllib import parse
import urllib3
import requests
from bs4 import BeautifulSoup

# requests를 이용한 수집 중 경고 해제.
urllib3.disable_warnings()

# MATERIALS: 수집에 필요한 준비물(api 키 등)을 보관하는 디렉토리.
# RESULTS: 수집 결과를 보관하는 디렉토리.
# VISUALIZATIONS: 시각화 결과를 보관하는 디렉토리.
MATERIALS = "materials"
RESULTS = "results"
VISUALIZATIONS = "visualizations"

# 뉴스 본문이 제대로 수집되었는지를 판단하기 위한 문서 길이.
# 글자수가 이 길이보다 적다면 제대로 수집되지 않은 것으로 판단한다.
NEWS_MAINTEXT_LOWER_BOUND = 300


class FileType(Enum):
    """
    수집한 데이터 파일의 종류를 지정하는 Enum 타입.
    데이터 수집 결과는 반드시 아래 타입 중 하나임.
    파일명은 f"{filetype.value}_{keyword}.txt" 형식 또는,
    키워드를 특정할 수 없는 경우 f"{filetype.value}.txt" 형식임.
    """

    # 실제로 사용되지 않음.
    # 뒤에 WT가 붙은 FileType은 본문 전문이 포함된 데이터셋임.
    # 뒤에 WT가 붙지 않은 FileType은 본문이 수집되지 않은 데이터셋임.
    WT = "_with_text"

    # 네이버 검색 API 뉴스, 지식IN 검색 결과.
    NEWS = RESULTS + "/" + "api_naver_news_result"
    NEWS_WT = NEWS + WT
    KIN = RESULTS + "/" + "api_naver_kin_result"
    KIN_WT = KIN + WT

    # 유사도 행렬 캐시 바이너리 파일.
    NEWS_SIM = RESULTS + "/" + "naver_news_similarity"
    KIN_SIM = RESULTS + "/" + "naver_kin_similarity"

    # 뉴스, 지식IN 크롤링 결과.
    CRAWL_NEWS = RESULTS + "/" + "crawl_naver_news_result"
    CRAWL_NEWS_WT = CRAWL_NEWS + WT
    CRAWL_KIN = RESULTS + "/" + "crawl_naver_kin_result"
    CRAWL_KIN_WT = CRAWL_KIN + WT

    # LLM 활용 관련도 검증 결과.
    NEWS_R = RESULTS + "/" + "naver_news_related"
    KIN_R = RESULTS + "/" + "naver_kin_related"

    # PROCESSED는 병합 및 토큰화가 완료된 파일임.
    # UNIQUE는 기준에 따라 중복 제거가 완료된 파일임.
    NEWS_PROCESSED = RESULTS + "/" + "naver_news_processed"
    NEWS_PROCESSED_UNIQUE = RESULTS + "/" + "naver_news_unique"
    KIN_PROCESSED = RESULTS + "/" + "naver_kin_processed"
    KIN_PROCESSED_UNIQUE = RESULTS + "/" + "naver_kin_unique"


def get_config() -> ConfigParser:
    """
    materials/config.ini 파일을 읽어들이는 함수.

    Returns:
        ConfigParser: config.ini의 내용을 담고 있는 ConfigParser 객체.
    """
    config = ConfigParser()
    config.read("materials/config.ini", encoding="utf8")
    return config


def get_id_secret() -> Tuple[str, str]:
    """
    materials/config.ini에서 네이버 API의 ID와 SECRET을 읽어들이는 함수.

    Returns:
        Tuple[str, str]: naver api를 위한 id, secret의 튜플.
    """
    config = get_config()
    return config["naver"]["id"], config["naver"]["secret"]


def get_key_org() -> Tuple[str, str]:
    """
    materials/config.ini에서 KEY와 ORGANIZATION을 읽어들이는 함수.

    Returns:
        Tuple[str, str]: openai api를 위한 key, organization의 튜플.
    """
    config = get_config()
    return config["openai"]["key"], config["openai"]["org"]


def get_request_cookie() -> str:
    """
    materials/config.ini에서 쿠키를 가져오는 함수.
    지식인 본문 수집 중 성인인증을 방지하기 위해 사용한다.

    Returns:
        str: 쿠키 문자열.
    """
    config = get_config()
    return config["browser"]["cookie"]


def get_typestring_from_filetype(filetype: FileType) -> str:
    """
    FileType Enum 객체에서 파일의 종류(기사/지식IN)를 나타내는 문자열을 반환한다.

    Args:
        filetype (FileType): 파일의 종류를 알고 싶은 FileType 객체.

    Returns:
        str: 파일의 종류에 따라 "news", "kin", "" 중 하나.
    """
    if "news" in filetype.value:
        return "news"
    if "kin" in filetype.value:
        return "kin"
    return ""


def get_filetype_from_typestring(typestring: str, additional_info: str) -> FileType:
    """
    파일 종류를 나타내는 문자열을 통해,
    FileType Enum 객체를 반환한다.

    TODO: 이런 방법보다는 FileType 객체를 Enum 객체가 아닌,
    제대로 된 속성을 가진 객체로 만들고,
    객체지향 관점으로 코드를 바꾸면 더 좋을 듯함.

    Args:
        typestring (str): 파일 종류를 나타내는 문자열("news" | "kin" | "").
        additional_info (str): 구체적인 파일 종류를 특정하기 위한 추가 문자열.
            - "api" | "wt" | "c" | "cwt" | "p" | "u" | "s"

    Returns:
        FileType: 파일의 종류에 맞는 FileType Enum 객체.
    """
    match (typestring, additional_info):
        case ("news", "" | "api"):
            return FileType.NEWS
        case ("news", "wt"):
            return FileType.NEWS_WT
        case ("news", "c"):
            return FileType.CRAWL_NEWS
        case ("news", "cwt"):
            return FileType.CRAWL_NEWS_WT
        case ("news", "r"):
            return FileType.NEWS_R
        case ("news", "p"):
            return FileType.NEWS_PROCESSED
        case ("news", "u"):
            return FileType.NEWS_PROCESSED_UNIQUE
        case ("news", "s"):
            return FileType.NEWS_SIM

        case ("kin", "" | "api"):
            return FileType.KIN
        case ("kin", "wt"):
            return FileType.KIN_WT
        case ("kin", "c"):
            return FileType.CRAWL_KIN
        case ("kin", "cwt"):
            return FileType.CRAWL_KIN_WT
        case ("kin", "r"):
            return FileType.KIN_R
        case ("kin", "p"):
            return FileType.KIN_PROCESSED
        case ("kin", "u"):
            return FileType.KIN_PROCESSED_UNIQUE
        case ("kin", "s"):
            return FileType.KIN_SIM


def validify_fname(fname: str) -> str:
    """
    fname에서 파일명에 사용할 수 없는 기호를 다른 문자로 대체한다.
    현재는 따옴표에 대해서만 작동.
        - " -> (quote)
        - ' -> (quote)

    Args:
        fname (str): 원래 파일명.

    Returns:
        str: 수정된 파일명.
    """

    return re.sub(r"[\"\']", "(quote)", fname)


def already(fname: str | List[str]) -> bool:
    """
    fname이 문자열이면, 현재 폴더에 파일명이 fname인 파일이 있는지 확인한다.
    fname이 리스트이면, 현재 폴더에서 fname 안의 모든 원소에 대해 확인한다.

    Args:
        fname (str | List[str]): 파일명 문자열(확장자 포함) 또는 파일명 문자열의 리스트.

    Returns:
        bool: 해당 파일들이 모두 이미 존재하는지의 여부.
    """
    if isinstance(fname, str):
        return path.exists(fname)
    return all(path.exists(fn) for fn in fname)


def search(
    base_url: str, query: str, api_id: str, secret: str, total_pages: int
) -> List[Dict[str, Optional[str]]]:
    """
    네이버 검색 api용 함수로, api 결과를 json으로 받을 것을 가정함.
    현재 네이버 뉴스 및 지식IN과 compatible.

    Args:
        base_url (str): api 기본 url.
        query (str): 검색할 키워드.
        id (str): naver api id.
        secret (str): naver api secret.
        total_pages (int): 한 페이지에 100개 결과가 있을 때, 총 페이지 수(최대 10 페이지 = 1000개).

    Returns:
        List[Dict[str, Optional[str]]]: [{아티클 0 정보}, {아티클 1 정보}, ...]
            ["title"]: 아티클의 제목(검색 키워드는 <b> 태그로 둘러쌓임).
            ["url_naver"]: 아티클의 주소, 뉴스인 경우 네이버 뉴스 주소(없으면 원본 기사 주소).
            ["url_original"]: 뉴스인 경우 원본 기사 주소, 지식IN이면 None.
            ["description"]: 아티클 본문에서 키워드가 등장한 부분의 패시지.
            ["date"]: 뉴스인 경우 뉴스의 날짜, 지식IN이면 None.
    """
    query = parse.quote(query)
    url = base_url + f"?query={query}&display=100"
    headers = {"X-Naver-Client-Id": api_id, "X-Naver-Client-Secret": secret}
    ret = []
    for page in range(total_pages):
        res = requests.get(url + f"&start={page * 100 + 1}", headers=headers, timeout=5)
        out_json = json.loads(res.text)
        for item in out_json["items"]:
            temp = {
                "title": item["title"],
                "url_naver": item["link"],
                "url_original": (
                    item["originallink"] if "originallink" in item else None
                ),
                "description": item["description"],
                "date": item["pubDate"] if "pubDate" in item else None,
            }
            ret.append(temp)
    return ret


def write_json_on_file(fname: str, wrapped: dict | list) -> None:
    """
    파일명이 fname인 파일을 만들어 wrapped를 json 형식으로 저장한다.

    Args:
        fname (str): 파일명 문자열(확장자 포함).
        wrapped (dict | list): json으로 덤프될 수 있는 딕셔너리, 리스트.
    """
    with open(fname, "wt", encoding="utf-8") as f:
        json.dump(wrapped, f, ensure_ascii=False, indent=4)


def get_json_from_file(fname: str) -> dict | list:
    """
    fname인 json 파일을 읽어서 파이썬 객체로 반환한다.

    Args:
        fname (str): 파일명 문자열(확장자 포함).

    Returns:
        dict | list: json 파일의 내용물을 파이썬 객체로 변환한 결과.
    """
    with open(fname, "rt", encoding="utf-8") as f:
        ret = json.load(f)
    return ret


def compare_encoding(a: Optional[str], b: Optional[str]) -> bool:
    """
    두 인코딩 문자열이 같은 인코딩을 지시하는지의 여부.


    Args:
        a (Optional[str]): 첫 번째 인코딩 문자열.
        b (Optional[str]): 두 번째 인코딩 문자열.

    Returns:
        bool: 둘 다 None이면 True, 그 외의 경우 같은 인코딩 문자열이어야 True.

    Usage:
        compare_encoding("utf-8", "utf8") -> True
        compare_encoding("cp949", "utf8") -> False
    """

    if a is None:
        return b is None
    a, b = a.lower().replace("-", "_"), b.lower().replace("-", "_")
    return aliases.get(a, a) == aliases.get(b, b)


def get_host_from_url(url: str) -> str:
    """
    url에서 www를 제외한 host 부분을 추출해냄.

    Args:
        url (str): 전체 url 문자열.

    Returns:
        str: 해당 url의 host 중 맨 앞의 "www."을 제외한 부분.
    """
    host = parse.urlparse(url).hostname
    if host.startswith("www."):
        host = host[4:]

    return host


def get_response_from_url(
    url: str, retry: int = 0, cookie: Optional[str] = None
) -> Optional[requests.models.Response]:
    """
    requests 모듈을 이용해 url에 get 요청을 보냄.
    User-Agent 헤더를 설정하고 올바른 요청을 받지 못하는 경우 None을 반환함.
    여러 번(기본은 1번만) 시도할 수 있으며, 2 ** (i - 1)초의 백오프가 발생함.
    데이터 수집의 용이성을 위해 SSL 인증이 꺼져 있으므로 인지할 것.

    Args:
        url (str): get 요청을 보낼 url.
        retry (int, optional): 요청이 실패한 경우 재시도할 횟수. 기본값은 0.
        cookie (Optional[str]): 쿠키를 설정한 경우 헤더에 쿠키를 추가해서 보냄.

    Returns:
        Optional[requests.models.Response]: 응답 결과인 requests 모듈의 response 객체거나, 올바르지 않은 결과인 경우 None.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }
    if cookie is not None:
        headers["Cookie"] = cookie

    for i in range(retry + 1):
        try:
            res = requests.get(
                url, headers=headers, timeout=5, verify=False, allow_redirects=True
            )
            res.raise_for_status()
            return res
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ):
            time.sleep(2 ** (i - 1))
    return None


def search_crawl(
    keyword: str, where: str, count: int = 300
) -> List[Dict[str, Optional[str]]]:
    """
    requests와 bs4를 통해 네이버 검색 결과를 직접 수집함.
    1990년부터 2024년까지, 각 년도별로 게시글을 수집함.
    현재는 네이버 뉴스만 지원함.

    Args:
        keyword (str): 검색 키워드.
        where (str): 수집할 데이터 종류(현재는 뉴스만 가능).
        count (int, optional): 각 년도별 검색결과 개수. 기본적으로는 년도별 300개.

    Returns:
        List[Dict[str, Optional[str]]]: [{아티클 0 정보}, {아티클 1 정보}, ...].
            ["title"]: 아티클의 제목(검색 키워드는 <b> 태그로 둘러쌓임).
            ["url_naver"]: 아티클의 주소.
            ["url_original"]: None.
            ["description"]: None.
            ["date"]: 아티클 날짜.
    """
    base_url = f"https://search.naver.com/search.naver?where={where}&query={keyword}"
    ret = []
    for year in range(1990, 2024):
        print(f"year {year} is starting...")
        for start in range(1, count, 10):
            time.sleep(0.5)
            url = base_url + f"&pd=3&ds={year}.01.01&de={year}.12.31&start={start}"
            res = get_response_from_url(url, 8)

            if res is None:
                return ret

            soup = BeautifulSoup(res.text, "html.parser")

            title_selector = "a.news_tit"
            temp_titles = soup.select(title_selector)
            if not temp_titles:
                break
            temp_dates = soup.select("span.info")

            titles = [x.get_text() for x in temp_titles]
            links = [x["href"] for x in temp_titles]
            dates = [
                parse_date_str(x.get_text())
                for x in temp_dates
                if parse_date_str(x.get_text())
            ]

            ret += [
                {
                    "title": title,
                    "url_naver": link,
                    "url_original": None,
                    "description": None,
                    "date": date,
                }
                for title, link, date in zip(titles, links, dates)
            ]
    return ret


def parse_date_str(cand: str) -> str:
    """
    날짜를 나타내는 문자열일 수 있는 후보 문자열을 받아서,
    날짜 문자열이거나 N일 전, N주 전이면 현재를 기준으로 해당하는 날짜를 문자열로 반환하고,
    그렇지 않으면 빈 문자열을 반환한다.

    Args:
        cand (str): 날짜 문자열로 추측되는 후보 문자열

    Returns:
        str: "%Y.%m.%d.", 즉 "YYYY.MM.DD."꼴의 날짜 문자열
    """
    try:
        ret = dt.datetime.strptime(cand, "%Y.%m.%d.")
    except ValueError:
        today = dt.date.today()
        if re.match(r"\d일 전", cand):
            ret = today - dt.timedelta(days=int(cand[0]))
        elif re.match(r"\d주 전", cand):
            ret = today - dt.timedelta(weeks=int(cand[0]))
        else:
            return ""
    return ret.strftime("%Y.%m.%d.")
