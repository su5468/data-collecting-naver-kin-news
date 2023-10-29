#!python
import json
import openai


def get_relatedness_list(articles: list, keyword, key: str, org: str) -> dict:
    INST = f"""기사의 제목과 내용의 일부분이 주어진다.
토픽이 "{keyword}"인지의 여부를 파악하라.
첫째 줄에 Y/N만을, 둘째 줄에 그 이유만을 간략하게 서술하고 그 외에 아무것도 작성하지 마라."""

    openai.organization = org
    openai.api_key = key

    base_query = [{"role": "system", "content": INST}]

    ret = {"tf": [], "reason": []}
    for i, article in enumerate(articles):
        content = f"제목 : {article['title']}\n내용 : {article['description']}"
        kwargs = {
            "model": "gpt-3.5-turbo",
            "messages": base_query + [{"role": "user", "content": content}],
            "temperature": 0.5,
        }
        try:
            res = openai.ChatCompletion.create(**kwargs)
        except Exception as err:
            print(f"error occures on {i}'s : {err}")
            return ret
        text = res["choices"][0]["message"]["content"]
        tf, *reason = text.split("\n")
        if tf == "Y":
            ret["tf"].append(True)
        elif tf == "N":
            ret["tf"].append(False)
        else:
            ret["tf"].append(True)
            print(f"exception case: {tf}")
        reason = "\n".join(reason).replace("이유:", "").strip()
        ret["reason"].append(reason)

        if i % 10 == 0:
            print(f"{i}'s complete")
    return ret


def main():
    keyword = "환자-의사 공유 의사결정"
    with open(f"api_naver_news_result_{keyword}.txt", encoding="utf-8") as f:
        articles = json.loads(f.read())["items"]

    with open("gpt_api_key.txt", encoding="utf-8") as f:
        KEY, ORG = map(lambda x: x.strip(), f.readlines())

    relatedness = get_relatedness_list(articles, keyword, KEY, ORG)

    # TODO : 중단된 경우 저장된 걸 불러와서 이어서 하도록 만들기

    with open(f"api_gpt_realtedness_result_{keyword}.txt", "wt", encoding="utf-8") as f:
        wrapped = {"keyword": keyword, "items": relatedness}
        json.dump(wrapped, f, ensure_ascii=False, indent=4)

    related_articles = []
    for i, e in enumerate(articles):
        if not relatedness["tf"][i]:
            continue
        related_articles.append(e)

    with open(f"new_result_related_{keyword}.txt", "wt", encoding="utf-8") as f:
        wrapped = {"keyword": keyword, "items": related_articles}
        json.dump(wrapped, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
