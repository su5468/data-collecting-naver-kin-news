#!python
# feel free to use this.
# if you have any question, contact me.
# 조건희( su5468@korea.ac.kr )

from typing import Set, Dict, List
import pickle
import utils


def get_similarity_matrix(
    articles: List[Dict[str, str | List[str]]]
) -> List[List[float]]:
    if utils.already(f"{utils.FileType.NEWS_SIM.value}.txt"):
        with open(f"{utils.FileType.NEWS_SIM.value}.txt", "rb") as f:
            return pickle.load(f)

    n = len(articles)
    similarity = [[1.0] * n for _ in range(n)]
    for i, article in enumerate(articles):
        if not i % 100:
            print(f"{i}'th similarity computed")
        for j in range(i + 1, n):
            a = set(article["tokens"])
            b = set(articles[j]["tokens"])
            similarity[i][j] = similarity[j][i] = jaccard(a, b)

    with open(f"{utils.FileType.NEWS_SIM.value}.txt", "wb") as f:
        pickle.dump(similarity, f)

    return similarity


def jaccard(a: Set[str], b: Set[str]) -> float:
    i, u = len(a & b), len(a | b)
    if not u:
        return 0
    return i / u


def main(filetype: utils.FileType) -> None:
    articles = utils.get_json_from_file(f"{filetype.value}.txt")["items"]
    n = len(articles)

    similarity = get_similarity_matrix(articles)
    to_del = []
    for i, line in enumerate(similarity):
        for j in range(i + 1, n):
            e = line[j]
            if e is not None and e > 0.5:
                d = j if len(articles[i]["text"]) > len(articles[j]["text"]) else i
                to_del.append(d)
                break

    for d in sorted(to_del, reverse=True):
        del articles[d]

    utils.write_json_on_file(
        f"{utils.FileType.NEWS_PROCESSED_UNIQUE.value}.txt",
        {"keyword": None, "items": articles},
    )


if __name__ == "__main__":
    main(utils.FileType.NEWS_PROCESSED)
