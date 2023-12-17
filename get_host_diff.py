#!python


def main(fname1: str, fname2: str) -> None:
    with open(fname1, "rt", encoding="utf8") as f:
        l1 = f.read().split("\n")
    with open(fname2, "rt", encoding="utf8") as f:
        l2 = f.read().split("\n")
    res = set(l1) - set(l2)
    with open(f"diff_{fname1}_{fname2}.txt", "wt", encoding="utf8") as f:
        print(*res, sep="\n", file=f)


if __name__ == "__main__":
    main(
        "hosts_crawl_naver_news_result_환자 의사 공유의사결정.txt",
        "hosts_api_naver_news_result_환자-의사 공유 의사결정.txt",
    )
