#!python

import re
import requests
from bs4 import BeautifulSoup
import utils


def get_answer_and_date(t: str) -> str:
    disclaimer = "(알아두세요!?\n([본위] 답변은.*|\n1.)|.*)"
    mat = re.match(
        r"(.*)" + disclaimer + r".*(\d{4}\.\d{2}\.\d{2})", t, re.DOTALL
    ).groups()
    return mat[0], mat[-1]


def get_kin_text_from_res(res: requests.models.Response) -> tuple:
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
            return "", ([], []), ""

    return (
        q.get_text(),
        zip(*[get_answer_and_date(e.get_text()) for e in a]),
        q_d.get_text()[3:],
    )


def get_kin_text_from_url(url: str) -> tuple:
    res = utils.get_response_from_url(url)
    if res is None:
        return "request_error", [], []
    q, (a, a_d), q_d = get_kin_text_from_res(res)
    if not q:
        return "encoding_error", [], []
    return q, list(a), [q_d] + list(a_d)


def main(keywords: list, force_redo: bool = False) -> None:
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

            if i == 5:
                break

        utils.write_json_on_file(fname, {"keyword": keyword, "items": articles})
        break


if __name__ == "__main__":
    main(["환자 의견", "환자 권리", "환자 요구"], True)
