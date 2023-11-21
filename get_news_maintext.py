#!python

import json
import gzip
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import utils


def get_news_text_from_url(url: str, failed_count: int) -> tuple:
    try:
        res = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            },
            timeout=5,
        )
        res.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
    ):
        temp.add(("", url, "to"))
        return "", failed_count + 1

    tested = False
    while True:
        try:
            rt = (
                gzip.decompress(res.content).decode("utf-8")
                if res.content.startswith(b"\x1f\x8b\x08")
                else res.text
            )
            soup = BeautifulSoup(rt, "html.parser")
            host = urlparse(url).hostname
            selector_dict = {
                "n.news.naver.com": "#dic_area",
                "www.newsprime.co.kr": "#news_body_area",
                "www.bokuennews.com": "#news_body_area",
                "akomnews.com": "#news_body_area",
                "www.cnbnews.com": "#news_body_area",
                "www.fetv.co.kr": "#news_body_area",
                "weekly.cnbnews.com": "#news_body_area",
                "www.ekn.kr": "#news_body_area_contents",
                "www.youthdaily.co.kr": "#news_bodyArea",
                "www.businesspost.co.kr": "#detail_tab_cont",
                "www.thebell.co.kr": "#article_main",
                "slownews.kr": "#pavo_contents",
                "www.boannews.com": "#news_content",
                "www.newspim.com": "#news-contents",
                "www.ebn.co.kr": "#newsContents",
                "fpn119.co.kr": "#textinput",
                "medicalworldnews.co.kr": "#viewContent",
                "www.dnews.co.kr": "#viewContent",
                "www.techholic.co.kr": "#articleBody",
                "www.hemophilia.co.kr": "#articleBody",
                "mdtoday.co.kr": "#articleBody",
                "www.ajunews.com": "#articleBody",
                "jhealthmedia.joins.com": "#articleBody",
                "monthly.chosun.com": "#articleBody",
                "www.kukinews.com": "#article",
                "magazine.hankyung.com": "#magazineView",
                "www.breaknews.com": "#CLtag",
                "www.thebigdata.co.kr": "#CmAdContent",
                "www.ifs.or.kr": "#bo_v_con",
                "www.yeongnam.com": "div.article-news-box",
                "kookbang.dema.mil.kr": "#article_body_view > p",
                "www.dailymedi.com": "#viewBody > div.varticle > div.arti",
                "dream.kotra.or.kr": "#pdfArea > dl > dd > div.view_txt",
                "www.korea.kr": "#container > div > div > div.article_body > div",
                "digitalchosun.dizzo.com": "#article > ul > li:nth-child(2) > div.cont_body",
                "byline.network": "#post-9004111222508021 > div > div.entry-content.single-content",
                "www.viva100.com": "#container > div.con_left > div.view_left_warp > div.left_text_box",
                "www.newstomato.com": "#main-top > section > div > div.rn_sontent.pt0px > section > div",
                "www.kpanews.co.kr": "#container > div > div.contents > div.bbs_cont.inr-c2 > div:nth-child(1)",
                "www.dentalnews.or.kr": "#container > div > div.column.sublay > div:nth-child(1) > div > div.arv_009_01 > div",
                "www.g-enews.com": "body > div.vcon > div.vcon_in > div.v_lt > div > div.mi_lt > div.v1d > div.vtxt.detailCont",
                "www.medigatenews.com": "body > div.container.sub > div.leftcont > div > div.content_print > div > div.contarea",
                "www.dailypharm.com": "body > div.wrap > div.newsBody > div.NewsCenterSide > div.d_newsContWrap > div.newsContents.font1",
                "www.medicaltimes.com": "#container > div > section.viewContWrap > div.viewCont_wrap > div.view_cont.ck-content.clearfix",
                "www.medipana.com": "#container > div.inr-c > div.flex_article > div.lft_article > div.bbs_view > div.cont > div.txt > div",
                "www.ciokorea.com": "body > div:nth-child(11) > div > div.col-lg-12.col-xl-9 > div > div.row > div:nth-child(2) > div.node-body",
                "news.mtn.co.kr": "#wrapper > div.theme-white > section > section.news-article-wrap > div.news-article-wrapper > div.news-content",
                "www.newsway.co.kr": "#container > div > section:nth-child(3) > div > div > div > div.content-left > div > article > div.view-text",
                "www.yakup.com": "#sub_con > div.contents_con.cf > div.left_con.layout_left_con > div > div > div.news_view_div > div.text_article_con",
                "www.lawtimes.co.kr": "#__next > div:nth-child(2) > div.css-8atqhb.e1s9yunr0 > div > div > div.css-i1madp.ehx2lg80 > div.css-ipsxml.e1ogx6dn0",
                "www.ceoscoredaily.com": "#container > div.inner > div.sticky_area_box > div.section.br > div > div.article_view.type_05 > div.article_content",
                "www.itworld.co.kr": "body > div:nth-child(11) > div > div.col-12.ps-lg-0.pe-lg-0 > div > div.section-content.col-12.col-lg.pe-lg-5 > div.node-body",
                "www.etoday.co.kr": "body > div.wrap > article.containerWrap > section.view_body_moduleWrap > div.l_content_module > div > div > div.view_contents > div.articleView",
                "biz.newdaily.co.kr": "body > div.nd-container.layout-center.border-none.clearfix.container-first.nd-news.sticky-container > section.nd-center > section > div:nth-child(2)",
            }

            selector = "#article-view-content-div"
            if host in selector_dict:
                selector = selector_dict[host]

            return soup.select_one(selector).get_text(), failed_count
        except AttributeError:
            if tested:
                temp.add((host, url, "pf"))
                return "", failed_count
            tested = True
            if res.encoding is None or res.encoding.lower() == "cp949":
                res.encoding = "utf-8"
            else:
                res.encoding = "cp949"


def main():
    keyword = "환자-의사 공유 의사결정"
    filetype = utils.FileType.API_NAVER_NEWS

    with open(f"{filetype.value}_{keyword}.txt", "rt", encoding="utf-8") as f:
        articles = json.load(f)["items"]

    global temp
    temp = set()
    failed = 0
    urls = utils.get_news_urls(keyword, filetype)
    for i, article in enumerate(articles):
        if i % 100 == 0:
            print(f"{i}'th article completed")
        url = urls[i]
        text, failed = get_news_text_from_url(url, failed)
        article["text"] = text

    with open(f"{filetype.value}_{keyword}_with_text.txt", "wt", encoding="utf-8") as f:
        wrapped = {"keyword": keyword, "items": articles}
        json.dump(wrapped, f, ensure_ascii=False, indent=4)

    print(temp, failed)


if __name__ == "__main__":
    main()
