#!python

from typing import List
import utils


def main(keywords: List[str], force_redo: bool = False) -> None:
    """
    네이버 지식IN 검색 api를 사용해서 키워드들의 검색 결과를 파일로 저장함.

    Args:
        keywords (List[str]): 키워드들의 리스트.
        force_redo (bool, optional): 이미 파일이 존재하는 경우에도 다시 수집할지의 여부. 기본적으로는 하지 않음.
    """
    url = "https://openapi.naver.com/v1/search/kin.json"
    num_of_pages = 10

    ID, SECRET = utils.get_id_secret()

    for keyword in keywords:
        fname = f"{utils.FileType.KIN.value}_{keyword}.txt"
        if not force_redo and utils.already(fname):
            continue

        search_result = utils.search(url, keyword, ID, SECRET, num_of_pages)

        utils.write_json_on_file(fname, {"keyword": keyword, "items": search_result})


if __name__ == "__main__":
    main(["환자 의견", "환자 권리", "환자 요구"])
