#!python

import utils


def main(keyword: str, filetype: utils.FileType) -> None:
    """
    script_가 접두사로 붙은 파일은,
    전체 수집, 분석 과정에서 불필요한,
    단순한 일회성 스크립트 파일임.
    굳이 살펴볼 필요는 없으나 혹시 재사용할 경우에 대비하여 기록.

    주어진 키워드와 FileType으로 알맞은 데이터를 찾아서,
    해당 파일의 호스트 목록을 파일로 저장함.

    Args:
        keyword (str): 검색 키워드 문자열.
        filetype (utils.FileType): FileType Enum 객체.
    """
    hosts = set()

    articles = utils.get_json_from_file(f"{filetype.value}_{keyword}.txt")["items"]
    for article in articles:
        url = article["url_naver"]
        host = utils.get_host_from_url(url)
        hosts.add(host)

    with open(f"hosts_{filetype.value}_{keyword}.txt", "wt", encoding="utf-8") as f:
        print(*hosts, sep="\n", file=f)


if __name__ == "__main__":
    main("환자 의사 공유의사결정", utils.FileType.CRAWL_NEWS)
