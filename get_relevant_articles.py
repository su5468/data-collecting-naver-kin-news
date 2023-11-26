#!python

import json
import asyncio
import openai
import utils


async def get_relatedness_list(
    articles: list, keyword: str, key: str, org: str
) -> dict:
    openai.organization = org
    openai.api_key = key

    INST = f"""기사의 제목과 내용의 일부분이 주어진다.
토픽이 "{keyword}"인지의 여부를 파악하라.
첫째 줄에 Y/N만을, 둘째 줄에 그 이유만을 간략하게 서술하고 그 외에 아무것도 작성하지 마라."""
    base_query = [{"role": "system", "content": INST}]

    ret = await asyncio.gather(
        *[
            get_nth_answer_async(
                i, article["title"], article["description"], base_query
            )
            for i, article in enumerate(articles)
        ]
    )
    return ret


async def get_nth_answer_async(
    i: int, title: str, description: str, base_query: list
) -> tuple:
    content = f"제목 : {title}\n내용 : {description}"
    kwargs = {
        "model": "gpt-3.5-turbo",
        "messages": base_query + [{"role": "user", "content": content}],
        "temperature": 0.5,
        "request_timeout": 30,
    }
    backoff = 5
    while True:
        try:
            res = await openai.ChatCompletion.acreate(**kwargs)
            break
        except Exception as err:
            print(
                f"error occures on {i}'s(will retry in 2**{backoff} seconds)\n : {err}"
            )
            await asyncio.sleep(2**backoff)
            backoff += 1

    text = res["choices"][0]["message"]["content"]
    tf, *reason = text.split("\n")

    if tf == "Y":
        tf = True
    elif tf == "N":
        tf = False
    else:
        print(f"exception case: {tf}")
        tf = True
    reason = "\n".join(reason).replace("이유:", "").strip()

    return tf, reason


async def main(
    keywords: list, filetype: utils.FileType, force_redo: bool = False
) -> None:
    wt = "with_text_" if filetype == utils.FileType.NEWS_WT else ""
    for keyword in keywords:
        fnames = (
            f"{utils.FileType.NEWS_RL.value}_{wt}{keyword}.txt",
            f"{utils.FileType.NEWS_R.value}_{wt}{keyword}.txt",
        )
        if not force_redo and utils.already(fnames):
            continue

        with open(f"{filetype.value}_{keyword}.txt", encoding="utf-8") as f:
            articles = json.loads(f.read())["items"]

        KEY, ORG = utils.get_key_org()

        relatedness, reasons = zip(
            *await get_relatedness_list(articles, keyword, KEY, ORG)
        )

        utils.write_json_on_file(
            fnames[0],
            wrapped={
                "keyword": keyword,
                "relatedness": relatedness,
                "reasons": reasons,
            },
        )

        related_articles = []
        for i, e in enumerate(articles):
            if not relatedness[i]:
                continue
            related_articles.append(e)

        utils.write_json_on_file(
            fnames[1], {"keyword": keyword, "items": related_articles}
        )


if __name__ == "__main__":
    asyncio.run(main(["환자-의사 공유 의사결정"], utils.FileType.NEWS))
