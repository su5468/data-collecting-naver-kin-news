#!python
# feel free to use this.
# if you have any question, contact me.
# 조건희( su5468@korea.ac.kr )

from typing import List
import utils


def main(keywords: List[str], force_redo: bool = False) -> None:
    for keyword in keywords:
        fname = f"{utils.FileType.CRAWL_NEWS.value}_{keyword}.txt"
        if not force_redo and utils.already(fname):
            continue

        search_result = utils.search_crawl(keyword, "news")

        utils.write_json_on_file(fname, {"keyword": keyword, "items": search_result})


if __name__ == "__main__":
    main(["환자 의사 공유의사결정"])
