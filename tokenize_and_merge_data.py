#!python

from typing import List, Tuple, Dict, Optional
from mecab import MeCab
import utils


def get_tokens(
    article: Dict[str, Optional[str | List[str]]], typestring: str
) -> Tuple[List[str], List[str]]:
    """
    기사 또는 지식IN 게시글 딕셔너리와 종류를 알려주는 문자열을 받아서,
    토큰화한 결과를 돌려준다.
    토크나이저는 python-mecab-ko의 mecab.MeCab을 사용했다.
    이 MeCab 라이브러리를 이용하면 윈도우에서도 간편하게 MeCab을 사용할 수 있지만,
    반대급부로 토큰화 속도가 매우 느리므로, 최적화의 여지가 있다.

    Args:
        article (Dict[str, Optional[str  |  List[str]]]): json 데이터 파일에서 불러온 게시글 하나의 딕셔너리.
        typestring (str): 파일 종류를 나타내는 문자열 "news" | "kin" | ...

    Returns:
        Tuple[List[str], List[str]]: 지식IN인 경우 (질문 토큰, 답변 토큰), 뉴스인 경우 (본문 토큰, 빈 리스트).
    """
    mecab = MeCab()
    if typestring == "news":
        return mecab.nouns(article["text"]), []
    if typestring == "kin":
        return (
            mecab.nouns(article["question"]),
            list(map(mecab.nouns, article["answers"])),
        )


def main(files: List[Tuple[utils.FileType, str]], save_file: utils.FileType) -> None:
    """
    파일들을 병합하고 토큰화하여,
    새로운 파일에 저장함.

    Args:
        files (List[Tuple[utils.FileType, str]]): FileType과 키워드들의 리스트.
        save_file (utils.FileType): 새로 저장할 파일을 결정하는 utils.FileType Enum 객체.
    """
    whole_articles = []
    for filetype, keyword in files:
        fname = filetype.value
        if keyword:
            fname += f"_{keyword}"
        fname = utils.validify_fname(f"{fname}.txt")
        articles = utils.get_json_from_file(fname)["items"]

        for i, article in enumerate(articles):
            if i % 100 == 0:
                print(f"{fname} : {i}'th article end")
            typestring = utils.get_typestring_from_filetype(filetype)
            if typestring == "news":
                article["tokens"], _ = get_tokens(article, typestring)
            elif typestring == "kin":
                article["tokens"], article["tokens_answer"] = get_tokens(
                    article, typestring
                )
            article["keyword"] = keyword
            article["source"] = filetype.value

        whole_articles += articles

    utils.write_json_on_file(
        f"{save_file.value}.txt",
        {"keyword": None, "items": whole_articles},
    )


if __name__ == "__main__":
    main(
        [
            (utils.FileType.KIN_WT, "환자 권리"),
            (utils.FileType.KIN_WT, "환자 요구"),
            (utils.FileType.KIN_WT, "환자 의견"),
        ],
        utils.FileType.KIN_PROCESSED,
    )
