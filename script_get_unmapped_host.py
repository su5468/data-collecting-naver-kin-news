#!python

import utils


def main(fname1: str, fname2: str) -> None:
    selector_dict = utils.get_json_from_file(
        f"{utils.MATERIALS}/news_maintext_selectors.txt"
    )
    articles = utils.get_json_from_file(fname2)["items"]
    with open(fname1, "rt", encoding="utf8") as f:
        l = f.read().split("\n")
    res = []
    for host in l:
        if host in selector_dict:
            continue
        if any(
            (
                host in article["url_naver"] and article["text"] != "encoding_error"
                for article in articles
            )
        ):
            continue
        res.append(host)
    with open(f"unmapped_{fname1}.txt", "wt", encoding="utf8") as f:
        print(*res, sep="\n", file=f)


if __name__ == "__main__":
    main(
        "hosts_crawl_naver_news_result_환자 의사 공유의사결정.txt",
        "crawl_naver_news_result_with_text_환자 의사 공유의사결정.txt",
    )
