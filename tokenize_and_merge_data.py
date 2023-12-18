#!python
# feel free to use this.
# if you have any question, contact me.
# 조건희( su5468@korea.ac.kr )

from typing import List, Tuple
from mecab import MeCab
import utils


def main(files: List[Tuple[utils.FileType, str]]) -> None:
    mecab = MeCab()
    whole_articles = []
    for filetype, keyword in files:
        articles = utils.get_json_from_file(f"{filetype.value}_{keyword}.txt")["items"]

        for i, article in enumerate(articles):
            if i % 100 == 0:
                print(f"{filetype.value}_{keyword}.txt : {i}'th article end")
            article["tokens"] = mecab.nouns(article["text"].strip())
            article["keyword"] = keyword
            article["source"] = filetype.value

        whole_articles += articles

    utils.write_json_on_file(
        f"{utils.FileType.NEWS_PROCESSED.value}.txt",
        {"keyword": None, "items": whole_articles},
    )


if __name__ == "__main__":
    main(
        [
            (utils.FileType.NEWS_WT, "환자-의사 공유 의사결정"),
            (utils.FileType.CRAWL_NEWS_WT, "환자 의사 공유의사결정"),
        ]
    )
