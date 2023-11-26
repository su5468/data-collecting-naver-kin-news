#!python

import utils


def main(keywords: list, force_redo: bool = False) -> None:
    url = "https://openapi.naver.com/v1/search/kin.json"
    num_of_pages = 10

    ID, SECRET = utils.get_id_secret()

    for keyword in keywords:
        fname = f"{utils.FileType.KIN.value}_{keyword}.txt"
        if not force_redo and utils.already(fname):
            continue

        search_result = utils.search(url, keyword, ID, SECRET, num_of_pages)

        utils.write_json_on_file(fname, {"keyword": keyword, "items": search_result})


if __name__ == "__main__":
    main(["환자 의견", "환자 권리", "환자 요구"])
