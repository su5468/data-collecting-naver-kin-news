#!python

from os import mkdir
import utils


def main(fname: str) -> None:
    """
    script_가 접두사로 붙은 파일은,
    전체 수집, 분석 과정에서 불필요한,
    단순한 일회성 스크립트 파일임.
    굳이 살펴볼 필요는 없으나 혹시 재사용할 경우에 대비하여 기록.

    주어진 본문이 있는 json 데이터셋에서,
    각 본문을 별개의 파일로 분리하여 저장함.

    Args:
        fname (str): 대상 파일 이름 문자열.
    """
    articles = utils.get_json_from_file(fname)["items"]
    for i, article in enumerate(articles):
        try:
            mkdir(f"{fname[:-4]}")
        except FileExistsError:
            pass
        with open(f"{fname[:-4]}/{i}.txt", "wt", encoding="utf-8") as f:
            f.write(article["text"])


if __name__ == "__main__":
    main(
        f"{utils.RESULTS}/crawl_naver_news_result_with_text_(quote)공유의사결정(quote).txt"
    )
