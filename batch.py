#!python

import re
import utils
import api_naver_news
import api_naver_kin
import get_news_maintext
import get_kin_maintext
import get_relevant_articles


def get_module_name(module):
    return re.findall(r"'(.+?)'", repr(module))[0]


def main():
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
    if order in "1r":
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
