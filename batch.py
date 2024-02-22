#!python

from typing import List, Tuple
from types import ModuleType
from collections import defaultdict
from itertools import product
import re
import utils
import api_naver_news
import api_naver_kin
import crawl_naver_news
import get_news_maintext
import get_kin_maintext
import tokenize_and_merge_data
import remove_similar_articles
import get_relevant_articles


def get_module_name(module: ModuleType) -> str:
    """
    모듈의 이름을 문자열로 반환
    이때, 모듈은 임포트되어 있어야 함

    Args:
        module (ModuleType): 모듈 객체

    Returns:
        str: 모듈의 이름

    Usage:
        get_module_name(re) -> "re"
    """
    return re.findall(r"'(.+?)'", repr(module))[0]


def get_keyword_conversational() -> List[str]:
    """
    사용자의 입력을 받아서,
    한 줄에 하나씩 문자열의 리스트로 반환한다.

    Returns:
        List[str]: 사용자의 입력을 리스트로 변환한 것.
    """
    ret = []
    while True:
        keyword = input("키워드: ")
        if not keyword:
            if confirm_conversational("키워드 입력을 완료했나요?"):
                return ret
            continue
        ret.append(keyword)


def confirm_conversational(
    prompt: str = "확실합니까?",
    yes: Tuple[str] = ("y", "t"),
    no: Tuple[str] = ("n", "f"),
    case_sensitive: bool = False,
    rigid: bool = False,
) -> bool:
    """
    사용자의 입력을 받아서,
    yes에 해당하면 True를 반환한다.
    그렇지 않으면 False를 반환한다.
    no에 해당하는지 확인하고 싶으면,
    rigid를 True로 한다.

    Args:
        prompt (str, optional): 입력을 받을 때 나타날 프롬프트. 선택지는 생략할 것.
        yes (Tuple[str], optional): True로 판정되는 문자열의 튜플. 기본은 ("y", "t").
        no (Tuple[str], optional): rigid == True인 경우 False로 판정되는 문자열의 튜플. 기본은 ("n", "f").
        case_sensitive (bool, optional): 대소문자를 구별하는지의 여부.
        rigid (bool, optional): 이 값이 False면 yes에 해당하지 않는 모든 값은 False, 이 값이 True면 no에 해당하는 값만 False.

    Raises:
        ValueError: rigid == True일 때, yes에도 no에도 없는 값을 입력받은 경우.

    Returns:
        bool: 사용자의 입력이 참인지 거짓인지의 여부.
    """
    if case_sensitive:
        preprocess_func = lambda x: x.lower()
    else:
        preprocess_func = lambda x: x

    yes = tuple(map(preprocess_func, yes))
    no = tuple(map(preprocess_func, no))
    answer = preprocess_func(
        input(f"{prompt} [{','.join(yes)} / {','.join(no)}]").strip()
    )
    if answer in yes:
        return True
    if not rigid or answer in no:
        return False
    raise ValueError("주어진 선택지의 값이 아닙니다!")


def main():
    """
    SDM 데이터 수집 과정 전체를 실행

    현재 과정:
        1. api_naver_news.py: 네이버 뉴스 검색 api로 뉴스 관련 데이터 수집.
        2. crawl_naver_news.py: 네이버 뉴스 검색결과 크롤링으로 뉴스 관련 데이터 수집.
        3. get_news_maintext.py: 뉴스 본문 스크래핑.
        4. api_naver_kin.py: 네이버 지식IN 검색 api로 지식IN 관련 데이터 수집.
        5. get_kin_maintext.py: 지식IN 본문 스크래핑.
        6. tokenize_and_merge_data.py: 뉴스 및 지식IN 데이터 토큰화하고 각각 하나의 데이터셋으로 병합.
        7. remove_similar_articles.py: 뉴스 및 지식IN 데이터 각각 유사도 검정하여 유사한 데이터 제거.
        8. get_relevant_articles.py: 뉴스 및 지식IN 데이터 각각 유관한 데이터만 필터링.


    세부적인 사항은 대화식으로 결정됨:
        1. procced: "T", "t", "Y", "y"가 아니면 현재 과정을 건너뛰고 다음 과정으로 넘어가고,
            "FORCE" 또는 "force"면 이미 수집한 파일도 다시 수집함
    """
    print(
        " 검색 키워드를 설정합니다.\n한 줄에 하나씩 키워드를 입력하고,\n설정이 완료되면 아무것도 입력하지 말고 엔터를 누르십시오."
    )
    keywords = {}
    print("<뉴스 키워드 설정>")
    keywords["news"] = get_keyword_conversational()
    print("<지식IN 키워드 설정>")
    keywords["kin"] = get_keyword_conversational()

    parent_keyword = input(
        "마지막으로, 이 데이터 전체를 아우르는 단 하나의 키워드는 무엇입니까?: "
    )
    parent_description = input(
        "그 키워드에 대해 가능한 자세히 한 줄로 설명해 주십시오: "
    )

    modules = [
        api_naver_news,
        crawl_naver_news,
        get_news_maintext,
        api_naver_kin,
        get_kin_maintext,
        tokenize_and_merge_data,
        remove_similar_articles,
        get_relevant_articles,
    ]
    module_iter_nums = defaultdict(lambda: 1)

    module_iter_nums[get_news_maintext] = 2
    module_iter_nums[tokenize_and_merge_data] = 2
    module_iter_nums[remove_similar_articles] = 2
    module_iter_nums[get_relevant_articles] = 2

    steps_list = ["news"] * 4 + ["kin"] * 2 + ["news", "kin"] * 3
    steps = {
        module: [None for _ in range(module_iter_nums[module])] for module in modules
    }
    temp = 0
    for module in steps:
        for i, _ in enumerate(steps[module]):
            steps[module][i] = steps_list[temp]
            temp += 1

    kwargs = {e: [{} for _ in range(module_iter_nums[e])] for e in modules}
    kwargs[api_naver_news][0]["keywords"] = keywords["news"]
    kwargs[crawl_naver_news][0]["keywords"] = keywords["news"]
    kwargs[get_news_maintext][0]["keywords"] = keywords["news"]
    kwargs[api_naver_kin][0]["keywords"] = keywords["kin"]
    kwargs[get_kin_maintext][0]["keywords"] = keywords["kin"]

    kwargs[get_news_maintext][0]["filetype"] = utils.FileType.NEWS
    kwargs[get_news_maintext][1]["filetype"] = utils.FileType.CRAWL_NEWS

    kwargs[tokenize_and_merge_data][0]["files"] = list(
        product([utils.FileType.NEWS, utils.FileType.CRAWL_NEWS], keywords["news"])
    )
    kwargs[tokenize_and_merge_data][0]["save_file"] = utils.FileType.NEWS_PROCESSED
    kwargs[tokenize_and_merge_data][1]["files"] = list(
        product([utils.FileType.KIN], keywords["kin"])
    )
    kwargs[tokenize_and_merge_data][1]["save_file"] = utils.FileType.KIN_PROCESSED

    kwargs[remove_similar_articles][0]["filetype"] = utils.FileType.NEWS_PROCESSED
    kwargs[remove_similar_articles][0]["method"] = "jaccard"
    kwargs[remove_similar_articles][1]["filetype"] = utils.FileType.KIN_PROCESSED
    kwargs[remove_similar_articles][1]["method"] = "url"

    kwargs[get_relevant_articles][0]["keyword"] = parent_keyword
    kwargs[get_relevant_articles][0]["description"] = parent_description
    kwargs[get_relevant_articles][0]["filetype"] = utils.FileType.NEWS_PROCESSED_UNIQUE
    kwargs[get_relevant_articles][1]["keyword"] = parent_keyword
    kwargs[get_relevant_articles][1]["description"] = parent_description
    kwargs[get_relevant_articles][1]["filetype"] = utils.FileType.KIN_PROCESSED_UNIQUE

    for module in modules:
        for i in range(module_iter_nums[module]):
            print(
                f"""'{get_module_name(module)}'의 {i + 1}번째 과정이 아래 키워드를 기반으로 수행됩니다.
동의하면 T, 이 과정을 생략하고 싶으면 F를 선택하십시오.
이 과정이 이미 수행되어 파일이 존재할 때, 재시도하고 싶으면 FORCE를 입력하십시오.
그렇게 하지 않으면 이미 있는 파일을 재사용합니다. [T/F/FORCE]"""
            )
            print(*keywords[steps[module][i]], sep="\n")
            procced = input()
            if procced.lower() not in ("t", "y"):
                continue

            force_redo = procced.lower() == "force"

            module.main(**kwargs[module][i], force_redo=force_redo)


if __name__ == "__main__":
    main()
