#!python
# feel free to use this.
# if you have any question, contact me.
# 조건희( su5468@korea.ac.kr )

from typing import List, Dict, Tuple, Optional
import re
import requests
from bs4 import BeautifulSoup
import utils


def get_answer_and_date(t: str) -> Tuple[str, str]:
    """
    정규표현식에 기반해 지식IN 답변 문자열을 답변 본문과 날짜로 분리함
    TODO: 정규표현식보다 본문의 태그를 살려서 bs4로 파싱하도록 리팩토링하는 게 좋을 듯

    Args:
        t (str): 지식IN 답변 문자열

    Returns:
        Tuple[str, str]: 답변 본문과 그 답변이 달린 날짜의 튜플
    """
    disclaimer = "(알아두세요!?\n([본위] 답변은.*|\n1.)|.*)"
    mat = re.match(
        r"(.*)" + disclaimer + r".*(\d{4}\.\d{2}\.\d{2})", t, re.DOTALL
    ).groups()
    return mat[0], mat[-1]


def get_kin_text_from_res(
    res: requests.models.Response,
) -> Tuple[Tuple[str, str], Tuple[List[str], List[str]]]:
    """
    requests의 응답(response) 객체에서 지식IN 텍스트를 추출

    Args:
        res (requests.models.Response): 지식IN 질문 링크로의 get 응답

    Returns:
        Tuple[str, str, Tuple[List[str], List[str]]]: (질문 본문, 질문 날짜, [응답 본문들], [응답 날짜들])
    """
    soup = BeautifulSoup(res.text, "html.parser")

    with open("temp.txt", "wt", encoding="utf8") as f:
        f.write(res.text)

    q_selector = "div.c-heading__content"
    a_selector = "div._endContents"
    q_d_selector = "span.c-userinfo__info"
    q = soup.select_one(q_selector)
    a = soup.select(a_selector)
    q_d = soup.select_one(q_d_selector)

    if q is None:
        q = soup.select_one("div.c-heading__title")
        if q is None:
            return ("", ""), ([], [])

    return (
        (q.get_text(), q_d.get_text()[3:]),
        tuple(zip(*[get_answer_and_date(e.get_text()) for e in a])),
    )


def get_kin_text_from_url(url: str) -> Tuple[str, List[str], List[str]]:
    """
    지식인 질문답변 url에서 질문, 답변, 날짜들의 리스트 반환

    Args:
        url (str): 지식인 질문 url

    Returns:
        Tuple[str, List[str], List[str]]: (질문 본문, [답변 본문들], [질문 날짜, 답변 날짜들])
    """
    res = utils.get_response_from_url(url)
    if res is None:
        return "request_error", [], []
    (q, q_d), (a, a_d) = get_kin_text_from_res(res)
    if not q:
        return "encoding_error", [], []
    return q, list(a), [q_d] + list(a_d)


def main(keywords: List[str], force_redo: bool = False) -> None:
    """
    키워드들을 가지고 지식IN 링크들에서 본문 추출
    먼저 검색 api(api_naver_kin.py)를 통해 검색 결과를 수집해야 함

    Args:
        keywords (List[str]): 키워드들의 리스트
        force_redo (bool, optional): 이미 파일이 존재하는 경우에도 다시 수집할지의 여부. 기본적으로는 하지 않음
    """
    for keyword in keywords:
        fname = f"{utils.FileType.KIN_WT.value}_{keyword}.txt"
        if not force_redo and utils.already(fname):
            continue

        articles = utils.get_json_from_file(f"{utils.FileType.KIN.value}_{keyword}.txt")
        for i, article in enumerate(articles):
            if i % 100 == 0:
                print(f"{i}'th article completed")
            url = article["url_naver"]
            q, a, d = get_kin_text_from_url(url)

            article["question"] = q
            article["answers"] = a
            article["date"] = d

            # TODO: 실험용 코드
            if i == 5:
                break

        utils.write_json_on_file(fname, {"keyword": keyword, "items": articles})
        break


if __name__ == "__main__":
    # TODO: 실험용 코드
    main(["환자 의견", "환자 권리", "환자 요구"], True)
