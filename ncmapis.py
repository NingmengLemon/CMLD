import json
from urllib import parse
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup as BS
from retry import retry

RETRY_TIME = 3

HEADERS = {
    "Host": "music.163.com",
    "Referer": "https://music.163.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
}

global_session = requests.Session()


def get_str(
    url: str,
    headers: Optional[dict[str, Any]] = None,
    session: Optional[requests.Session] = None,
    **kwargs,
):
    if headers is None:
        kwargs["headers"] = HEADERS.copy()
    kwargs.setdefault("timeout", 10)
    session = global_session if session is None else session
    with session.get(url, **kwargs) as resp:
        resp.raise_for_status()
        return resp.text


@retry(tries=RETRY_TIME, delay=0.5)
def get_info(mid: int) -> dict[str, Any]:
    url = "https://music.163.com/song?id={mid}".format(mid=mid)
    bs = BS(get_str(url), "html.parser")
    res = {
        "title": bs.find("em", class_="f-ff2").get_text(),
        "artists": [
            i.get_text()
            for i in bs.find_all("p", class_="des s-fc4")[0].find_all(
                "a", class_="s-fc7"
            )
        ],
        #'subtitle':bs.find('div',class_='subtit f-fs1 f-ff2').get_text(),
        "cover": bs.find("img", class_="j-img").attrs["data-src"],
        "mid": int(mid),
    }
    try:
        res["album"] = (
            bs.find_all("p", class_="des s-fc4")[1].find("a", class_="s-fc7").get_text()
        )
        res["album_id"] = int(
            bs.find_all("p", class_="des s-fc4")[1]
            .find("a", class_="s-fc7")
            .attrs["href"]
            .split("?id=")[-1]
        )
    except IndexError:
        res["album"] = None
        res["album_id"] = None
    return res


@retry(tries=RETRY_TIME, delay=0.5)
def get_album(aid: int) -> dict:
    url = "https://music.163.com/album?id={aid}".format(aid=aid)
    bs = BS(get_str(url), "html.parser")
    data = json.loads(bs.find("textarea", id="song-list-pre-data").get_text())
    res = {
        "music_list": [
            {
                "order": i["no"],
                "title": i["name"],
                "mid": i["id"],
                "artists": [a["name"] for a in i["artists"]],
            }
            for i in data
        ],
        "aid": aid,
        "title": bs.find("h2", class_="f-ff2").get_text(),
        "artists": [
            i.get_text()
            for i in bs.find("p", class_="intr").find_all("a", class_="s-fc7")
        ],
    }
    return res


@retry(tries=RETRY_TIME, delay=0.5)
def search_music(*kws, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
    url = "https://music.163.com/api/search/get/?s={}&limit={}&type=1&offset={}".format(
        "+".join([parse.quote(kw) for kw in kws]), limit, offset
    )
    data = json.loads(get_str(url))
    if "result" not in data:
        return []
    if "songs" not in data["result"]:
        return []
    res = [
        {
            "mid": i["id"],
            "title": i["name"],
            "artists": [a["name"] for a in i["artists"]],
            "album": i["album"]["name"],
            "album_id": i["album"]["id"],
            #'trans_titles':i['transNames'],
        }
        for i in data["result"]["songs"]
    ]
    return res


@retry(tries=RETRY_TIME, delay=0.5)
def get_lyrics(mid: int) -> tuple[Optional[str], Optional[str]]:
    """
    返回一个元组, 第一个项是原文, 第二个项是翻译
    没有的用 None 占位
    """
    api = f"https://music.163.com/api/song/lyric?id={str(mid)}&lv=-1&kv=-1&tv=-1"
    data = json.loads(get_str(api))
    if "lrc" in data:
        lyrics = data["lrc"]["lyric"]
        if "tlyric" in data:
            if tl := data["tlyric"]["lyric"].strip():
                lyrics_trans = tl
            else:
                lyrics_trans = None
        else:
            lyrics_trans = None
    else:
        lyrics = lyrics_trans = None
    return lyrics, lyrics_trans
