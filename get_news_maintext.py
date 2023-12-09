#!python

import gzip
import time
import re
import requests
from bs4 import BeautifulSoup
import utils


def get_news_text_from_res_and_url(url: str, res: requests.models.Response) -> str:
    text = (
        gzip.decompress(res.content).decode("utf-8")
        if res.content.startswith(b"\x1f\x8b\x08")
        else res.text
    )

    host = utils.get_host_from_url(url)
    selectors = get_news_selector_from_host(host)

    soup = BeautifulSoup(text, "html.parser")
    for selector in selectors:
        result = soup.select_one(selector)
        if result is None:
            continue
        return get_text_from_soup(soup.select_one(selector), host)

    return ""


def get_redirection_link(url: str) -> str:
    url_dict = {
        "thebell.co.kr": (
            r"key=(\d+)",
            "http://www.thebell.co.kr/free/content/ArticleView.asp?key=",
            "&svccode=00&page=1&sort=thebell_check_time",
        )
    }

    host = utils.get_host_from_url(url)
    if host not in url_dict:
        return url

    pat, pre, post = url_dict[host]
    key = re.search(pat, url).group(1)
    return pre + key + post


def get_text_from_soup(soup: BeautifulSoup, host: str) -> str:
    getter_attr_dict = {"lawtimes.co.kr": "content"}

    key = getter_attr_dict.get(host, "")
    if not key:
        return soup.get_text()
    return soup[key]


def get_news_selector_from_host(host: str) -> str:
    selector_dict = {
        "n.news.naver.com": ["#dic_area"],
        "asiatoday.co.kr": ["#font"],
        "smartfn.co.kr": ["#body_wrap"],
        "newsprime.co.kr": ["#news_body_area"],
        "bokuennews.com": ["#news_body_area"],
        "akomnews.com": ["#news_body_area"],
        "cnbnews.com": ["#news_body_area"],
        "fetv.co.kr": ["#news_body_area"],
        "theguru.co.kr": ["#news_body_area"],
        "weekly.cnbnews.com": ["#news_body_area"],
        "tfmedia.co.kr": ["#news_body_area"],
        "geconomy.co.kr": ["#news_body_area"],
        "kgnews.co.kr": ["#news_body_area"],
        "ekn.kr": ["#news_body_area_contents"],
        "youthdaily.co.kr": ["#news_bodyArea"],
        "businesspost.co.kr": ["#detail_tab_cont", "div.detail_editor"],
        "thebell.co.kr": ["#article_main"],
        "weeklytrade.co.kr": ["#article_text"],
        "slownews.kr": ["#pavo_contents"],
        "boannews.com": ["#news_content"],
        "newspim.com": ["#news-contents"],
        "ebn.co.kr": ["#newsContents"],
        "fpn119.co.kr": ["#textinput"],
        "newscham.net": ["#news-article-content"],
        "medicalworldnews.co.kr": ["#viewContent"],
        "dnews.co.kr": ["#viewContent", "div.text"],
        "upinews.kr": ["#viewConts"],
        "siminilbo.co.kr": ["#viewConts"],
        "artinsight.co.kr": ["#view_content"],
        "metroseoul.co.kr": ["div.col-12"],
        "techholic.co.kr": ["#articleBody"],
        "hemophilia.co.kr": ["#articleBody"],
        "fntimes.com": ["#articleBody"],
        "wsobi.com": ["#articleBody"],
        "mdtoday.co.kr": ["#articleBody"],
        "economychosun.com": ["#articleBody"],
        "ajunews.com": ["#articleBody"],
        "mediapen.com": ["#articleBody"],
        "jhealthmedia.joins.com": ["#articleBody"],
        "monthly.chosun.com": ["#articleBody"],
        "kukinews.com": ["#article"],
        "investchosun.com": ["#article"],
        "newdaily.co.kr": ["#ndArtBody"],
        "ciokorea.com": ["div.node-body"],
        "itworld.co.kr": ["div.node-body"],
        "news2day.co.kr": ["div.view_con"],
        "magazine.hankyung.com": ["#magazineView"],
        "breaknews.com": ["#CLtag"],
        "thebigdata.co.kr": ["#CmAdContent"],
        "lawissue.co.kr": ["#CmAdContent"],
        "ifs.or.kr": ["#bo_v_con"],
        "whosaeng.com": ["#textinput"],
        "topdaily.kr": ["div.content"],
        "dailyvet.co.kr": ["div.pf-content"],
        "medigatenews.com": ["div.contarea"],
        "kpenews.com": ["div.cont-area"],
        "platum.kr": ["div.single"],
        "skyedaily.com": ["div.articletext"],
        "catholictimes.org": ["div.detail-story"],
        "lawtimes.co.kr": ["meta:nth-child(4)"],
        "yeongnam.com": ["div.article-news-box"],
        "wikitree.co.kr": ["div.article_body"],
        "mdilbo.com": ["div.article_body"],
        "dailypharm.com": ["div.newsContents.font1"],
        "dealsite.co.kr": ["div.rnmc-full"],
        "harpersbazaar.co.kr": ["div.atc_content"],
        "yakup.com": ["div.text_article_con"],
        "sentv.co.kr": ["section.section_2"],
        "kookbang.dema.mil.kr": ["#article_body_view > p"],
        "byline.network": ["div.entry-content.single-content"],
        "dailymedi.com": ["#viewBody > div.varticle > div.arti"],
        "dream.kotra.or.kr": ["#pdfArea > dl > dd > div.view_txt"],
        "asiatime.co.kr": ["div.row.article_txt_container > div"],
        "korea.kr": ["#container > div > div > div.article_body > div"],
        "digitalchosun.dizzo.com": ["#article > ul > li:nth-child(2) > div.cont_body"],
        "biz.newdaily.co.kr": ["section.nd-news-body > div:nth-child(2)"],
        "viva100.com": [
            "#container > div.con_left > div.view_left_warp > div.left_text_box"
        ],
        "newstomato.com": [
            "#main-top > section > div > div.rn_sontent.pt0px > section > div"
        ],
        "kpanews.co.kr": [
            "#container > div > div.contents > div.bbs_cont.inr-c2 > div:nth-child(1)"
        ],
        "dentalnews.or.kr": [
            "#container > div > div.column.sublay > div:nth-child(1) > div > div.arv_009_01 > div"
        ],
        "g-enews.com": [
            "body > div.vcon > div.vcon_in > div.v_lt > div > div.mi_lt > div.v1d > div.vtxt.detailCont"
        ],
        "medicaltimes.com": [
            "#container > div > section.viewContWrap > div.viewCont_wrap > div.view_cont.ck-content.clearfix"
        ],
        "medipana.com": [
            "#container > div.inr-c > div.flex_article > div.lft_article > div.bbs_view > div.cont > div.txt > div"
        ],
        "news.mtn.co.kr": [
            "#wrapper > div.theme-white > section > section.news-article-wrap > div.news-article-wrapper > div.news-content"
        ],
        "newsway.co.kr": [
            "#container > div > section:nth-child(3) > div > div > div > div.content-left > div > article > div.view-text"
        ],
        "ceoscoredaily.com": [
            "#container > div.inner > div.sticky_area_box > div.section.br > div > div.article_view.type_05 > div.article_content"
        ],
        "etoday.co.kr": [
            "body > div.wrap > article.containerWrap > section.view_body_moduleWrap > div.l_content_module > div > div > div.view_contents > div.articleView"
        ],
    }

    selector = selector_dict.get(host, ["#article-view-content-div"])

    return selector


def get_news_text_from_url(url: str) -> str:
    url = get_redirection_link(url)
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
                errors[text].append((i, url))

            article["text"] = text

        print("processing failed requests...")
        time.sleep(5)
        for i in range(3):
            time.sleep(1)
            for i, (article_idx, url) in enumerate(errors["request_error"]):
                text = get_news_text_from_url(url)
                articles[article_idx]["text"] = text
                if text in errors:
                    continue
                del errors["request_error"][i]

        utils.write_json_on_file(fname, {"keyword": keyword, "items": articles})

        print(errors)
        print(len(errors["encoding_error"]))


if __name__ == "__main__":
    main(["환자-의사 공유 의사결정"], utils.FileType.NEWS, True)
