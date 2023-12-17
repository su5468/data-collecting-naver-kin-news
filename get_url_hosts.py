#!python

import utils


def main():
    hosts = set()
    keyword = "환자 의사 공유의사결정"
    filetype = utils.FileType.CRAWL_NEWS

    articles = utils.get_json_from_file(f"{filetype.value}_{keyword}.txt")["items"]
    for article in articles:
        url = article["url_naver"]
        host = utils.get_host_from_url(url)
        hosts.add(host)

    with open(f"hosts_{filetype.value}_{keyword}.txt", "wt", encoding="utf-8") as f:
        print(*hosts, sep="\n", file=f)


if __name__ == "__main__":
    main()
