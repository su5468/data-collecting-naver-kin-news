#!python
import json
import asyncio
import openai


async def get_relatedness_list(articles: list, keyword, key: str, org: str) -> dict:
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
        "request_timeout": 60,
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


async def main():
    keyword = "환자-의사 공유 의사결정"
    with open(f"api_naver_news_result_{keyword}.txt", encoding="utf-8") as f:
        articles = json.loads(f.read())["items"]

    with open("gpt_api_key.txt", encoding="utf-8") as f:
        KEY, ORG = map(lambda x: x.strip(), f.readlines())

    relatedness, reasons = zip(*await get_relatedness_list(articles, keyword, KEY, ORG))

    with open(f"api_gpt_realtedness_result_{keyword}.txt", "wt", encoding="utf-8") as f:
        wrapped = {"keyword": keyword, "relatedness": relatedness, "reasons": reasons}
        json.dump(wrapped, f, ensure_ascii=False, indent=4)

    related_articles = []
    for i, e in enumerate(articles):
        if not relatedness[i]:
            continue
        related_articles.append(e)

    with open(f"new_result_related_{keyword}.txt", "wt", encoding="utf-8") as f:
        wrapped = {"keyword": keyword, "items": related_articles}
        json.dump(wrapped, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
