import os
import re
import sys
import time
import json
from io import BytesIO
import winreg
import logging
from functools import wraps
from urllib import parse

from bs4 import BeautifulSoup as BS
from retry import retry

import requester as reqer

retry_time = 3


def auto_retry(retry_time: int = retry_time):
    def retry_decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            _run_counter = 0
            while True:
                _run_counter += 1
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print("Error:", e, "Retrying...")
                    # raise e
                    if _run_counter > retry_time:
                        raise e

        return wrapped

    return retry_decorator


# @auto_retry()
@retry(tries=retry_time, delay=0.5)
def get_info(mid: int) -> dict:
    url = "https://music.163.com/song?id={mid}".format(mid=mid)
    bs = BS(reqer.get_str(url), "html.parser")
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


# @auto_retry()
@retry(tries=retry_time, delay=0.5)
def get_album(aid: int) -> dict:
    url = "https://music.163.com/album?id={aid}".format(aid=aid)
    bs = BS(reqer.get_str(url), "html.parser")
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


# @auto_retry()
@retry(tries=retry_time, delay=0.5)
def search_music(*kws, limit: int = 10, offset: int = 0) -> dict:
    url = "https://music.163.com/api/search/get/?s={}&limit={}&type=1&offset={}".format(
        "+".join([parse.quote(kw) for kw in kws]), limit, offset
    )
    data = json.loads(reqer.get_str(url))
    if "result" not in data:
        return []
    if "songs" in data["result"]:
        res = [
            {
                "mid": i["id"],
                "title": i["name"],
                "artists": [a["name"] for a in i["artists"]],
                "album": i["album"]["name"],
                "album_id": i["album"]["id"]
                #'trans_titles':i['transNames'],
            }
            for i in data["result"]["songs"]
        ]
        return res
    else:
        return []


# @auto_retry()
@retry(tries=retry_time, delay=0.5)
def get_lyrics(mid: int) -> tuple:
    """
    返回一个元组, 第一个项是原文, 第二个项是翻译
    没有的用 None 占位
    """
    api = f"https://music.163.com/api/song/lyric?id={str(mid)}&lv=-1&kv=-1&tv=-1"
    data = json.loads(reqer.get_str(api))
    if "lrc" in data:
        lyrics = data["lrc"]["lyric"]
        if "tlyric" in data:
            if data["tlyric"]["lyric"].strip():
                lyrics_trans = data["tlyric"]["lyric"]
            else:
                lyrics_trans = None
        else:
            lyrics_trans = None
    else:
        lyrics = lyrics_trans = None
    return lyrics, lyrics_trans
