#!python

from collections import defaultdict
import utils


def main(fname: str):
    selector_dict = utils.get_json_from_file(
        f"{utils.MATERIALS}/news_maintext_selectors.txt"
    )
    selector_dict = defaultdict(list, selector_dict)

    with open(fname, "rt", encoding="utf8") as f:
        for line in f:
            host, *selectors = line.split()
            if not selectors:
                continue
            selector_dict[host].append(" ".join(selectors))
    utils.write_json_on_file(
        f"{utils.MATERIALS}/news_maintext_selectors1.txt", selector_dict
    )


if __name__ == "__main__":
    main("unmapped_hosts_crawl_naver_news_result_환자 의사 공유의사결정.txt.txt")
