#!python

from typing import List
import utils


def main(keywords: List[str], force_redo: bool = False) -> None:
    """
    웹 크롤링(스크래핑)을 통해 키워드들의 검색 결과를 파일로 저장함.

    Args:
        keywords (List[str]): 키워드들의 리스트.
        force_redo (bool, optional): 이미 파일이 존재하는 경우에도 다시 수집할지의 여부. 기본적으로는 하지 않음.
    """
    for keyword in keywords:
        fname = utils.validify_fname(f"{utils.FileType.CRAWL_NEWS.value}_{keyword}.txt")
        if not force_redo and utils.already(fname):
            continue

        search_result = utils.search_crawl(keyword, "news")

        utils.write_json_on_file(fname, {"keyword": keyword, "items": search_result})


if __name__ == "__main__":
    main(['"환자 이해"', '"의료 의사 결정"', '"환자의사결정"'])
