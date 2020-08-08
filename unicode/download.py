import logging
import os
import pathlib
import zipfile

import requests
import requests_ftp  # type: ignore

from unicode.version import __user_agent__

requests_ftp.monkeypatch_session()

BLOCKS_TARGET = "Blocks.txt"
CASEFOLDING_TARGET = "CaseFolding.txt"
CONFUSABLES_TARGET = "confusables.txt"
HANGUL_TARGET = "hangul.txt"
NAMESLIST_TARGET = "NamesList.txt"
UNIHAN_READINGS_TARGET = "Unihan_Readings.txt"
UNIHAN_TARGET = "Unihan.zip"
WIKIPEDIA_TARGET = "wikipedia.html"

UNICODE = "13.0.0"
BLOCKS_URL = f"ftp://www.unicode.org/Public/{UNICODE}/ucd/Blocks.txt"
CASEFOLDING_URL = f"ftp://www.unicode.org/Public/{UNICODE}/ucd/CaseFolding.txt"
CONFUSABLES_URL = f"ftp://ftp.unicode.org/Public/security/{UNICODE}/confusables.txt"
HANGUL_URL = "https://raw.githubusercontent.com/whatwg/encoding/master/index-euc-kr.txt"
NAMESLIST_URL = f"ftp://www.unicode.org/Public/{UNICODE}/ucd/NamesList.txt"
UNIHAN_URL = f"ftp://www.unicode.org/Public/{UNICODE}/ucd/Unihan.zip"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Unicode_block"


def fetch_data_files(cache_dir: str, reset_cache: bool) -> None:
    if reset_cache:
        for file_name in [
            BLOCKS_TARGET,
            CASEFOLDING_TARGET,
            CONFUSABLES_TARGET,
            HANGUL_TARGET,
            NAMESLIST_TARGET,
            UNIHAN_READINGS_TARGET,
            UNIHAN_TARGET,
            WIKIPEDIA_TARGET,
        ]:
            path = os.path.join(cache_dir, file_name)
            if os.path.isfile(path):
                os.remove(path)
    download(BLOCKS_URL, os.path.join(cache_dir, BLOCKS_TARGET))
    download(CASEFOLDING_URL, os.path.join(cache_dir, CASEFOLDING_TARGET))
    download(CONFUSABLES_URL, os.path.join(cache_dir, CONFUSABLES_TARGET))
    download(HANGUL_URL, os.path.join(cache_dir, HANGUL_TARGET))
    download(NAMESLIST_URL, os.path.join(cache_dir, NAMESLIST_TARGET))
    download(UNIHAN_URL, os.path.join(cache_dir, UNIHAN_TARGET))
    download(WIKIPEDIA_URL, os.path.join(cache_dir, WIKIPEDIA_TARGET))
    unzip(os.path.join(cache_dir, UNIHAN_TARGET), cache_dir)


def download(url: str, cache_file_name: str) -> None:
    if os.path.isfile(cache_file_name):
        return

    logging.info("downloading: %s", url)
    if url.startswith("ftp:"):
        ftp_session = requests.Session()
        res = ftp_session.get(url)
    else:
        res = requests.get(url, headers={"user-agent": __user_agent__})

    if res.status_code == requests.codes.ok:
        data = res.content
    else:
        raise RuntimeError(f"downloading {url} yields {res.status_code}")

    pathlib.Path(os.path.dirname(cache_file_name)).mkdir(parents=True, exist_ok=True)
    with open(cache_file_name, "wb") as f:
        f.write(data)


def unzip(zip_file_name: str, target_dir: str) -> None:
    with zipfile.ZipFile(zip_file_name, "r") as f:
        f.extractall(target_dir)
