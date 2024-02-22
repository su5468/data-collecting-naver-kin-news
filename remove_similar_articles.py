#!python

from typing import Set, Dict, List, Optional
import pickle
from urllib.parse import urlparse, parse_qs
import numpy as np
import utils


def get_similarity_matrix(
    articles: List[Dict[str, Optional[str | List[str] | List[List[str]]]]],
    typestring: str,
    method: str,
    force_redo: bool,
) -> List[List[float]]:
    """
    유사도 계산 방법에 기반하여,
    각 게시글(아티클)별 유사도를 전부 계산한다.
    이미 캐시된 파일이 있으면 이를 사용한다.
    내부적으로 유사도 계산을 2차원 리스트로 하고 있는데,
    numpy ndarray를 사용하면 개선이 가능할 수 있으므로 참고.

    Args:
        articles (List[Dict[str, Optional[str | List[str] | List[List[str]]]]]): json 데이터 파일에서 가져온 아티클 리스트.
        typestring (str): 파일 종류를 나타내는 문자열. "news" | "kin"
        method (str): 유사도 계산 방법을 나타내는 문자열. "jaccard" | "url".
        force_redo (bool): 캐시된 파일을 재사용하지 않고 새로 계산할지의 여부.
        - 기본은 True이며, 파일타입만 가지고 캐시의 존재여부를 확인하므로 의도적이지 않은 경우 True로 하는 것이 좋음.

    Returns:
        List[List[float]]: 유사도들의 2차원 리스트.
    """
    fname = utils.get_filetype_from_typestring(typestring, "s").value + f"_{method}"
    if not force_redo and utils.already(f"{fname}.txt"):
        with open(f"{fname}.txt", "rb") as f:
            return pickle.load(f)

    n = len(articles)
    similarity = [[1.0] * n for _ in range(n)]
    for i, article in enumerate(articles):
        if not i % 100:
            print(f"{i}'th similarity computed")
        if method == "jaccard":
            a = np.array(article["tokens"])
        elif method == "mixed":
            a = np.array(article["tokens_answer"])
        for j in range(i + 1, n):
            if method == "jaccard":
                b = np.array(set(articles[j]["tokens"]))
                similarity[i][j] = similarity[j][i] = jaccard(a, b)
            if method == "url":
                similarity[i][j] = similarity[j][i] = url_match(
                    article["url_naver"], articles[j]["url_naver"]
                )

    with open(f"{fname}.txt", "wb") as f:
        pickle.dump(similarity, f)

    return similarity


def url_match(a: str, b: str) -> int:
    """
    url에서 dirId와 docId가 같으면 1.
    아니면 0을 유사도로 반환한다.
    두 지식IN 게시글이 같은 스레드를 가리키는지 확인할 때 사용.

    Args:
        a (str): 첫 번째 url.
        b (str): 두 번째 url.

    Returns:
        int: 유사도 0 | 1.
    """
    a_params = parse_qs(urlparse(a).query)
    b_params = parse_qs(urlparse(b).query)

    a_id = a_params["dirId"], a_params["docId"]
    b_id = b_params["dirId"], b_params["docId"]
    if a_id == b_id:
        return 1
    return 0


def jaccard(a: Set[str], b: Set[str]) -> float:
    """
    두 집합에 대해,
    자카드 유사도를 계산한다.
    자카드 유사도는 두 집합의 교집합 / 합집합으로 계산된다.
    두 게시글(아티클)의 토큰 유사도를 확인할 때 사용.

    Args:
        a (Set[str]): 첫 번째 집합.
        b (Set[str]): 두 번째 집합.

    Returns:
        float: 자카드 유사도.
    """
    i = np.intersect1d(a, b).size
    u = a.size + b.size - i
    if not u:
        return 0
    return i / u


def main(filetype: utils.FileType, method: str, force_redo: bool = True) -> None:
    """
    지정된 유사도 계산 방법에 따라 유사도를 계산하고
    다른 게시글과의 유사도가 0.5 이상인 게시글(아티클)은
    더 짧은 쪽을 드랍한다.

    Args:
        filetype (utils.FileType): 파일의 종류를 나타내는 utils.FileType 객체.
        method (str): 유사도 계산 방법. "jaccard" | "url".
        force_redo (bool, optional): 이미 캐시된 유사도 행렬 파일이 있을 때 이를 재계산할지의 여부.
        - 기본은 True이며, 파일타입만 가지고 캐시의 존재여부를 확인하므로 의도적이지 않은 경우 True로 하는 것이 좋음.
    """
    articles = utils.get_json_from_file(f"{filetype.value}.txt")["items"]
    n = len(articles)
    typestring = utils.get_typestring_from_filetype(filetype)

    similarity = get_similarity_matrix(articles, typestring, method, force_redo)
    to_del = []
    for i, line in enumerate(similarity):
        for j in range(i + 1, n):
            e = line[j]
            if e is not None and e > 0.5:
                if typestring == "news":
                    d = j if len(articles[i]["text"]) > len(articles[j]["text"]) else i
                elif typestring == "kin":
                    d = j
                to_del.append(d)
                break

    for d in sorted(to_del, reverse=True):
        del articles[d]

    filetype = utils.get_filetype_from_typestring(typestring, "u")
    utils.write_json_on_file(
        f"{filetype.value}.txt",
        {"keyword": None, "items": articles},
    )


if __name__ == "__main__":
    main(utils.FileType.KIN_PROCESSED, "url")
    # main(utils.FileType.NEWS_PROCESSED, "jaccard")
