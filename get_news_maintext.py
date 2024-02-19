#!python

from typing import List, Dict, Set

import gzip
import time
import re
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import utils


def get_news_text_from_res(
    res: requests.models.Response, maps: Dict[str, Dict[str, str] | Set[str]]
) -> str:
    """
    requests 모듈의 응답 객체(Response)를 이용해서 뉴스 본문을 추출.
    응답이 gzip으로 압축되어 있는 경우가 있어 확인한 후 압축을 해제함.

    Args:
        res (requests.models.Response): requests 모듈의 응답 객체.
        maps (Dict[str, Dict[str, str] | Set[str]]): css 셀렉터, 리디렉션, 본문이 들어있는 태그 속성 딕셔너리들.

    Returns:
        str: 뉴스 기사 본문.
    """
    text = (
        gzip.decompress(res.content).decode("utf-8")
        if res.content.startswith(b"\x1f\x8b\x08")
        else res.text
    )

    url = res.url
    host = utils.get_host_from_url(url)
    selectors = get_news_selector_from_host(host, maps["selector"])

    soup = BeautifulSoup(text, "html.parser")
    for selector in selectors:
        result = soup.select_one(selector)
        if result is None:
            continue
        ret = get_text_from_soup(result, host, maps["attribute"])
        if len(ret) < utils.NEWS_MAINTEXT_LOWER_BOUND:
            continue
        return get_text_from_soup(result, host, maps["attribute"])

    for selector in maps["selector_set"]:
        result = soup.select_one(selector)
        if result is None:
            continue
        ret = get_text_from_soup(result, host, maps["attribute"])
        if len(ret) < utils.NEWS_MAINTEXT_LOWER_BOUND:
            continue
        maps["selector"][host].append(selector)
        return ret

    return ""


def get_redirection_link(url: str, redirect_dict: Dict[str, str]) -> str:
    """
    많은 리디렉션이 일어나 일반적으로 수집할 수 없거나, 감지할 수 없는 리디렉션이 있거나(주로 js를 이용한),
    기타 다른 링크를 활용해야 하는 상황에서 현재 url을 리디렉션이 완료된 url로 바꿈.
    이 과정은 redirect_dict의 매핑에 의해 이루어짐.

    Args:
        url (str): 원래 기사 url.

    Returns:
        str: 리디렉션 결과로 변환된 기사 url.
    """

    host = utils.get_host_from_url(url)
    if host not in redirect_dict:
        return url

    pats, pre, post = redirect_dict[host]
    for pat in pats:
        key = re.search(pat, url)
        if key is None:
            continue
        key = key.group(1)
        return pre + key + post
    return url


def get_text_from_soup(
    soup: BeautifulSoup, host: str, attr_dict: Dict[str, str]
) -> str:
    """
    css 셀렉터를 이용해 추출된 bs 객체에서, 기사 텍스트만 추출하고 스트립함.
    기본 동작은 soup.get_text()를 이용해 태그가 없는 텍스트만 추출.
    다만, 일부 기사는 태그 내부 속성(attribute)에 기사 본문이 있는 경우가 있음.
    이 경우 attr_dict의 매핑에 기반해서 해당 속성의 값 추출.

    Args:
        soup (BeautifulSoup): 셀렉터를 이용해 필터링이 완료된 bs 객체.
        host (str): 기사 사이트 호스트.
        attr_dict (Dict[str, str]): 호스트별 본문이 들어있는 태그 속성 매핑 딕셔너리.

    Returns:
        str: 기사 본문 문자열.
    """

    key = attr_dict.get(host, "")
    if not key:
        return soup.get_text().strip()
    return soup[key].strip()


def get_news_selector_from_host(host: str, selector_dict: Dict[str, str]) -> List[str]:
    """
    selector_dict의 매핑과 기사 호스트를 통해 해당하는 css 셀렉터 리스트를 추출함.
    결과는 셀렉터 문자열의 리스트인데, 일부 사이트는 기사마다 셀렉터가 달라서 그럼.
    만약 그 파일에 답이 없으면 가장 자주 쓰이는 것으로 보이는 ["#article-view-content-div"]를 반환.

    Args:
        host (str): 기사 사이트의 url 호스트.
        selector_dict (Dict[str, str]): 호스트별 셀렉터 매핑 딕셔너리.

    Returns:
        List[str]: css 셀렉터들의 리스트.
    """

    selector = selector_dict.get(host, ["#article-view-content-div"])

    return selector


def get_news_text_from_url(url: str, maps: Dict[str, Dict[str, str] | Set[str]]) -> str:
    """
    url에서 뉴스 기사 본문을 추출함.
    사이트에서 제대로 된 응답을 받지 못하면 "request error"를,
    파싱이나 기사 본문 추출을 제대로 하지 못하면 "encoding error"를 반환.

    Args:
        url (str): 기사 url.
        maps (Dict[str, Dict[str, str] | Set[str]]): css 셀렉터, 리디렉션, 본문이 들어있는 태그 속성 딕셔너리들.

    Returns:
        str: 기사 본문 문자열.
    """
    url = get_redirection_link(url, maps["redirect"])
    res = utils.get_response_from_url(url)
    if res is None:
        return "request_error"
    text = get_news_text_from_res(res, maps)
    if not text:
        return "encoding_error"
    return text


def main(keywords: list, filetype: utils.FileType, force_redo: bool = False) -> None:
    """
    키워드들을 가지고, 그 키워드에 대한 기사 링크 데이터를 찾아서,
    본문을 추가해 json 형태로 새로운 파일에 저장함.

    Args:
        keywords (List[str]): 키워드들의 리스트.
        filetype (utils.FileType): 기사 링크 데이터의 파일타입(utils.py 참조).
        force_redo (bool, optional): 이미 파일이 존재하는 경우에도 다시 수집할지의 여부. 기본적으로는 하지 않음.
    """
    maps = {
        "selector": utils.get_json_from_file(
            f"{utils.MATERIALS}/news_maintext_selectors.txt"
        ),
        "redirect": utils.get_json_from_file(
            f"{utils.MATERIALS}/news_maintext_redirections.txt"
        ),
        "attribute": utils.get_json_from_file(
            f"{utils.MATERIALS}/news_maintext_attributes.txt"
        ),
    }
    maps["selector"] = defaultdict(list, maps["selector"])
    maps["selector_set"] = set(sum(maps["selector"].values(), []))
    maps["selector_set"].add("#article-view-content-div")

    for keyword in keywords:
        errors = {"request_error": [], "encoding_error": []}
        fname = utils.validify_fname(f"{filetype.value}_with_text_{keyword}.txt")
        if not force_redo and utils.already(fname):
            continue

        original_fname = utils.validify_fname(f"{filetype.value}_{keyword}.txt")
        articles = utils.get_json_from_file(original_fname)["items"]
        for i, article in enumerate(articles):
            if i % 100 == 0:
                print(f"{i}'th article completed")
            url = article["url_naver"]
            text = get_news_text_from_url(url, maps)

            if text in errors:
                errors[text].append((i, url))

            article["text"] = text

        print("processing failed requests...")
        time.sleep(5)
        for i in range(3):
            time.sleep(1)
            del_list = []
            for i, (article_idx, url) in enumerate(errors["request_error"]):
                text = get_news_text_from_url(url, maps)
                articles[article_idx]["text"] = text
                if text in errors:
                    continue
                del_list.append(i)
            for i in del_list[::-1]:
                del errors["request_error"][i]

        utils.write_json_on_file(fname, {"keyword": keyword, "items": articles})
        utils.write_json_on_file(
            f"{utils.MATERIALS}/news_maintext_selectors.txt", maps["selector"]
        )


if __name__ == "__main__":
    main(
        ['"환자 이해"', '"의료 의사 결정"', '"환자의사결정"'],
        utils.FileType.CRAWL_NEWS,
        False,
    )
