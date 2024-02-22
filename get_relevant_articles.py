#!python

from typing import List, Dict, Tuple, Callable, Optional
from random import random
from functools import wraps
import asyncio
from httpx import Timeout
from openai import AsyncOpenAI
import utils


async def get_relatedness_list(
    articles: List[Dict[str, Optional[str | List[str] | List[List[str]]]]],
    keyword: str,
    description: str,
    key: str,
    org: str,
) -> List[Tuple[bool, str]]:

    client = AsyncOpenAI(
        api_key=key,
        organization=org,
        timeout=Timeout(15.0, read=5.0, write=10.0, connect=3.0),
    )

    INST = f"""기사 또는 게시글의 제목과 내용이 주어진다.
해당 게시글의 토픽이 "{keyword}"과 연관성을 가지고 있는지 파악하라.
"{keyword}"란, {description}
첫째 줄에 Y/N만을, 둘째 줄에 그 이유만을 간략하게 서술하고 그 외에 아무것도 작성하지 마라."""
    base_query = [{"role": "system", "content": INST}]

    global tried_articles, succed_articles
    tried_articles = 0
    succed_articles = 0

    n = len(articles)
    ret = []
    for i in range(0, n, 30):
        chunk = articles[i : min(i + 30, n)]
        ret += await asyncio.gather(
            *[
                get_nth_answer_async(
                    client, j, article["title"], get_all_text(article), base_query
                )
                for j, article in enumerate(chunk)
            ]
        )
    return ret


def get_all_text(
    article: Dict[str, Optional[str | List[str] | List[List[str]]]]
) -> str:
    """
    게시글(아티클)의 전체 내용을 하나의 문자열로 반환함.

    Args:
        article (Dict[str, Optional[str  |  List[str]  |  List[List[str]]]]): 단일 게시글(아티클) 딕셔너리.

    Returns:
        str: 해당 아티클의 본문 문자열.
    """
    if "text" in article:
        return article["text"]
    ret = f"질문: {article['question']}"
    for i, answer in enumerate(article["answers"]):
        ret += f"\n답변 {i}: {answer}"
    return ret


def length_filter_decorator(l: int = 10000) -> Callable[[Callable], Callable]:
    """
    get_nth_answer_async()에서,
    텍스트 길이가 토큰 제한을 넘을 것 같으면,
    실행하지 않고 유관한 것으로 간주하고 반환한다.
    이러한 아티클에 대해서는 수동으로 확인해야 함.
    gpt-3.5-turbo의 토큰 제한은 대략 16000 정도이고,
    한글은 받침이 없으면 1토큰, 있으면 2토큰이므로,
    넉넉하게 10000자 정도는 수용 가능하다.

    Args:
        l (int, optional): 게시글(아티클)의 최대 길이. 기본값 10000.

    Returns:
        Callable[[Callable], Callable]: 데코레이터 래퍼 함수.
    """

    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            if "text" in kwargs:
                text = kwargs["text"]
            else:
                text = args[3]
            if len(text) > l:
                return True, "길이 초과로 직접 확인 필요."
            return await f(*args, **kwargs)

        return wrapper

    return decorator


@length_filter_decorator(10000)
async def get_nth_answer_async(
    client: AsyncOpenAI, i: int, title: str, text: str, base_query: List[Dict[str, str]]
) -> Tuple[bool, str]:
    """
    OpenAI API 요청을 통해서 연관성을 확인함.

    Args:
        client (AsyncOpenAI): OpenAI 요청 클라이언트 객체(비동기).
        i (int): 해당 게시글(아티클)의 인덱스
        title (str): _description_
        text (str): _description_
        base_query (List[Dict[str, str]]): _description_

    Returns:
        Tuple[bool, str]: _description_
    """
    global tried_articles, succed_articles

    content = f"제목 : {title}\n내용 : {text}"
    kwargs = {
        "model": "gpt-3.5-turbo",
        "messages": base_query + [{"role": "user", "content": content}],
        "temperature": 0.5,
    }
    backoff = 6
    tried_articles += 1
    if tried_articles % 100 == 0:
        print(f"[{succed_articles} / {tried_articles}]")
    while True:
        try:
            res = await client.chat.completions.create(**kwargs)
            break
        except Exception as err:
            print(
                f"error occures on {i}'s(will retry in about 2**{backoff} seconds [{succed_articles} / {tried_articles}])\n : {err}"
            )
            await asyncio.sleep(2**backoff + random() * 2)
            backoff += 1

    result = res.choices[0].message.content
    tf, *reason = result.split("\n")

    if tf.upper() == "Y":
        tf = True
    elif tf.upper() == "N":
        tf = False
    else:
        print(f"exception case: {tf}")
        tf = True
    reason = "\n".join(reason).replace("이유:", "").strip()

    succed_articles += 1
    if succed_articles % 100 == 0:
        print(f"[{succed_articles} / {tried_articles}]")

    return tf, reason


async def main(
    keyword: str, description: str, filetype: utils.FileType, force_redo: bool = False
) -> None:
    """
    게시글(아티클)의 데이터셋에서,
    해당 키워드와 유관한 것들만 골라낸다.
    OpenAI API를 이용한다.

    Args:
        keyword (str): 데이터셋의 중심이 되는 하나의 키워드.
        description (str): 해당 키워드에 대한 긴 글 설명.
        filetype (utils.FileType): 필터링 전 데이터셋의 utils.FileType Enum 객체.
        force_redo (bool, optional): 이미 필터링 결과가 있어도 강제로 다시할지의 여부. 기본값은 거짓.
    """
    typestring = utils.get_typestring_from_filetype(filetype)
    result_filetype = utils.get_filetype_from_typestring(typestring, "r")
    fname = f"{result_filetype.value}.txt"
    if not force_redo and utils.already(fname):
        return

    articles = utils.get_json_from_file(f"{filetype.value}.txt")["items"]

    KEY, ORG = utils.get_key_org()

    relatedness, reasons = zip(
        *await get_relatedness_list(articles, keyword, description, KEY, ORG)
    )

    related_articles = []
    for i, e in enumerate(articles):
        if not relatedness[i]:
            continue
        related_articles.append(e)

    utils.write_json_on_file(
        fname,
        wrapped={
            "keyword": keyword,
            "items": related_articles,
            "relatedness": relatedness,
            "reasons": reasons,
        },
    )


if __name__ == "__main__":
    DESCRIPTION = "치료나 진료 등 의료행위에 있어서, 의사가 독단적으로 결정을 내리지 않고, 환자나 그 가족 등과 의사결정 과정을 공유하고 검토하는 것을 의미한다. 이를테면 연명의료(존엄사), 만성 질환에서 치료 방법, 또는 그 외의 모든 크고 작은 의료행위에 관하여 의료인이 환자와 그 가족의 방침과 의견을 적극 수용하는 것이 환자 의사 공유의사결정에 해당한다. 그 외에도 의사와 환자 사이 의사소통과 결정이 잘 이루어지도록 하는 정책, 사회적 분위기, 법률, 사상 등도 이와 연관이 있다. 이를테면 의사가 병의 양태와 처치 방법에 대하여 환자에게 설명하거나 환자의 선택권을 존중할 의무나, 그러한 설명의무를 법제화하는 논의 등도 환자 의사 공유의사결정과 관련 있다. 즉, 명시적으로 의사결정 과정이 드러나지 않더라도, 의료행위 또는 그 선택과 관련된 환자의 권리가 드러난다면 환자 의사 공유의사결정과 연관된 것으로 본다."
    EXAMPLES = "연관된 내용의 예시: 존엄사 결정, 질환 치료방법 선택, 환자의 알 권리, 의사의 설명의무, 환자와 의사의 의사소통, 환자의 자기결정권, 공유의사결정 관련 학회 및 담화 등"
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(
        main(
            "환자 의사 공유의사결정",
            DESCRIPTION + "\n" + EXAMPLES,
            utils.FileType.KIN_PROCESSED_UNIQUE,
            True,
        )
    )
