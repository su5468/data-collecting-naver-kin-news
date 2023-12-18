#!python

from collections import defaultdict
import utils


def main(fname):
    ret = defaultdict(list)
    articles = utils.get_json_from_file(fname)["items"]
    for article in articles:
        if len(article["text"]) > 400:
            continue
        url = article["url_naver"]
        host = utils.get_host_from_url(url)

        ret[host].append(url)

    utils.write_json_on_file(f"errors_{fname}.txt", ret)


if __name__ == "__main__":
    main("crawl_naver_news_result_with_text_환자 의사 공유의사결정.txt")
