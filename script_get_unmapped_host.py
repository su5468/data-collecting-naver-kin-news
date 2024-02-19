#!python

import utils


def main(fname_hosts: str, fname_data: str) -> None:
    """
    script_가 접두사로 붙은 파일은,
    전체 수집, 분석 과정에서 불필요한,
    단순한 일회성 스크립트 파일임.
    굳이 살펴볼 필요는 없으나 혹시 재사용할 경우에 대비하여 기록.

    호스트 목록 파일과 json 기사 데이터셋 파일을 가지고,
    호스트 목록 중 기사가 제대로 수집되지 않는 호스트들을 파일로 저장함.

    Args:
        fname_hosts (str): 호스트 목록 파일.
        fname_data (str): json 기사 데이터셋 파일.
    """
    selector_dict = utils.get_json_from_file(
        f"{utils.MATERIALS}/news_maintext_selectors.txt"
    )
    articles = utils.get_json_from_file(fname_data)["items"]
    with open(fname_hosts, "rt", encoding="utf8") as f:
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
    with open(f"unmapped_{fname_hosts}.txt", "wt", encoding="utf8") as f:
        print(*res, sep="\n", file=f)


if __name__ == "__main__":
    main(
        "hosts_crawl_naver_news_result_환자 의사 공유의사결정.txt",
        "crawl_naver_news_result_with_text_환자 의사 공유의사결정.txt",
    )
