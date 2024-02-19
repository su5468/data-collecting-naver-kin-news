#!python

from types import ModuleType
import re
import utils
import api_naver_news
import api_naver_kin
import get_news_maintext
import get_kin_maintext
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


def main():
    """
    SDM 데이터 수집 과정 전체를 실행

    현재 과정:
        1. api_naver_news.py: 네이버 뉴스 검색 api로 뉴스 관련 데이터 수집
        2. get_news_maintext.py: 뉴스 본문 스크래핑
        3. get_relevant_articles.py: 검색 결과중 키워드와 유관한 것만 필터링
        4. api_naver_kin.py: 네이버 지식IN 검색 api로 지식IN 관련 데이터 수집
        5. get_kin_maintext.py: 지식IN 본문 스크래핑


    세부적인 사항은 대화식으로 결정됨:
        1. order: "1", "R", 또는 "r"이면 뉴스 검색에서 본문 스크래핑보다 필터링을 먼저 함
        2. procced: "T", "t", "Y", "y"가 아니면 현재 과정을 건너뛰고 다음 과정으로 넘어가고,
            "FORCE" 또는 "force"면 이미 수집한 파일도 다시 수집함
    """
    news_keywords = ["환자-의사 공유 의사결정"]
    kin_keywords = ["환자 의견", "환자 권리", "환자 요구"]

    modules = [
        api_naver_news,
        get_news_maintext,
        get_relevant_articles,
        api_naver_kin,
        get_kin_maintext,
    ]
    keywords = [news_keywords] * 3 + [kin_keywords] * 2
    args = [[] for _ in modules]

    order = input("full-text first or relatedness first?[0/1]")
    if order.lower() in ("1", "r"):
        modules[1], modules[2] = modules[2], modules[1]
        args[1].append(utils.FileType.NEWS)
        args[2].append(utils.FileType.NEWS_R)
    else:
        args[1].append(utils.FileType.NEWS)
        args[2].append(utils.FileType.NEWS_WT)

    for i, module in enumerate(modules):
        print(
            f"'{get_module_name(module)}' for below keywords is going to run, continue? [T/F/FORCE]"
        )
        print(*keywords[i], sep="\n")
        procced = input()
        if procced.lower() not in ("t", "y"):
            continue

        force_redo = procced.lower() == "force"

        module.main(keywords[i], force_redo, *args[i])


if __name__ == "__main__":
    main()
