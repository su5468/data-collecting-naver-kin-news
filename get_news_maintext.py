#!python

import gzip
from urllib import parse
import requests
from bs4 import BeautifulSoup
import utils


def get_news_text_from_res_and_url(url: str, res: requests.models.Response) -> str:
    initial_encoding = res.encoding
    raw_text = (
        gzip.decompress(res.content).decode("utf-8")
        if res.content.startswith(b"\x1f\x8b\x08")
        else res.text
    )

    host = parse.urlparse(url).hostname
    selector = get_news_selector_from_host(host)

    encodings = ["utf8", None, "cp949"]
    for encoding in encodings:
        full_text = raw_text.encode(initial_encoding).decode(encoding)
        soup = BeautifulSoup(full_text, "html.parser")
        result = soup.select_one(selector)
        if result is None:
            continue
        return soup.select_one(selector).get_text()

    return ""


def get_news_selector_from_host(host: str) -> str:
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

    selector = selector_dict.get(host, "#article-view-content-div")

    return selector


def get_news_text_from_url(url: str) -> str:
    res = utils.get_response_from_url(url)
    if res is None:
        return "request_error"
    text = get_news_text_from_res_and_url(url, res)
    if not text:
        return "encoding_error"
    return text


def main(keywords: list, filetype: utils.FileType, force_redo: bool = False) -> None:
    errors = {"request_error": [], "encoding_error": []}

    for keyword in keywords:
        fname = f"{filetype.value}_with_text_{keyword}.txt"
        if not force_redo and utils.already(fname):
            continue

        articles = utils.get_json_from_file(f"{filetype.value}_{keyword}.txt")
        for i, article in enumerate(articles):
            if i % 100 == 0:
                print(f"{i}'th article completed")
            url = article["url_naver"]
            text = get_news_text_from_url(url)

            if text in errors:
                errors[text].append(url)

            article["text"] = text

        utils.write_json_on_file(fname, {"keyword": keyword, "items": articles})

        print(errors)


if __name__ == "__main__":
    main(["환자-의사 공유 의사결정"], utils.FileType.NEWS)
