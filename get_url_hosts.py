#!python

from urllib.parse import urlparse
import utils


def main():
    keyword = "환자-의사 공유 의사결정"
    filetype = utils.FileType.API_NAVER_NEWS

    urls = utils.get_news_urls(keyword, filetype)
    hosts = set((urlparse(url).hostname for url in urls))

    with open(f"hosts_{filetype.value}_{keyword}.txt", "wt", encoding="utf-8") as f:
        print(*hosts, sep="\n", file=f)


if __name__ == "__main__":
    main()
