#!python

from collections import defaultdict
import utils


def main(fname: str) -> None:
    """
    script_가 접두사로 붙은 파일은,
    전체 수집, 분석 과정에서 불필요한,
    단순한 일회성 스크립트 파일임.
    굳이 살펴볼 필요는 없으나 혹시 재사용할 경우에 대비하여 기록.

    `script_get_unmapped_host.py`에서 수집한 호스트들에 대해,
    수동으로 옆에 기사 본문에 대한 CSS 선택자를 적어준 후,
    실행해서 MATERIALS의 선택자 파일을 갱신해줄 수 있음.

    Args:
        fname (str): CSS 선택자를 적은 unmapped_hosts 파일 이름.
    """
    selector_dict = utils.get_json_from_file(
        f"{utils.MATERIALS}/news_maintext_selectors.txt"
    )
    selector_dict = defaultdict(list, selector_dict)

    with open(fname, "rt", encoding="utf8") as f:
        for line in f:
            host, *selectors = line.split()
            if not selectors:
                continue
            selector = " ".join(selectors)
            if selector in selector_dict[host]:
                continue
            selector_dict[host].append(selector)
    utils.write_json_on_file(
        f"{utils.MATERIALS}/news_maintext_selectors.txt", selector_dict
    )


if __name__ == "__main__":
    main("unmapped_hosts_crawl_naver_news_result_환자 의사 공유의사결정.txt.txt")
