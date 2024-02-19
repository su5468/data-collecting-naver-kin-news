#!python

from collections import defaultdict
import utils


def main(fname: str) -> None:
    """
    script_가 접두사로 붙은 파일은,
    전체 수집, 분석 과정에서 불필요한,
    단순한 일회성 스크립트 파일임.
    굳이 살펴볼 필요는 없으나 혹시 재사용할 경우에 대비하여 기록.

    본문이 수집된 데이터 중
    본문이 제대로 수집되지 않은 데이터의 호스트를 모두 수집함.

    Args:
        fname (str): 확인할 데이터셋 파일명.
    """
    ret = defaultdict(list)
    articles = utils.get_json_from_file(fname)["items"]
    for article in articles:
        if len(article["text"]) >= utils.NEWS_MAINTEXT_LOWER_BOUND:
            continue
        url = article["url_naver"]
        host = utils.get_host_from_url(url)

        ret[host].append(url)

    utils.write_json_on_file(f"errors_{fname}.txt", ret)


if __name__ == "__main__":
    main("crawl_naver_news_result_with_text_환자 의사 공유의사결정.txt")
