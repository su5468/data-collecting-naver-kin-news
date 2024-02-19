#!python


def main(fname1: str, fname2: str) -> None:
    """
    script_가 접두사로 붙은 파일은,
    전체 수집, 분석 과정에서 불필요한,
    단순한 일회성 스크립트 파일임.
    굳이 살펴볼 필요는 없으나 혹시 재사용할 경우에 대비하여 기록.

    get_url_hosts.py를 통해 생성된
    호스트 목록 파일 2개를 비교해서
    fname1에는 있고, fname2에는 없는
    호스트들을 모두 저장함.

    Args:
        fname1 (str): 호스트 목록 파일명 1.
        fname2 (str): 호스트 목록 파일명 2.
    """
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
