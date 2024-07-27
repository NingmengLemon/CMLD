from typing import Optional
import re
import logging
import os

import unicodedata

import ncmkey
from tinytag import TinyTag
from fuzzyfinder import fuzzyfinder as fuzzy_match


REGEX_TRACK_PREFIX = r"^(\d+\.?\s*)+\s+"


def normalize(text: str) -> str:
    return replace_char(unicodedata.normalize("NFKC", text).strip())


def replace_char(text: str) -> str:
    chr_table = {
        "/": "／",
        "*": "＊",
        ":": "：",
        "\\": "＼",
        ">": "＞",
        "<": "＜",
        "|": "｜",
        "?": "？",
        '"': "＂",
    }
    for t in list(chr_table.keys()):
        text = text.replace(t, chr_table[t])
    return text


def handle_artists_from_tag(artists: list[str]) -> list[str]:
    if not artists:
        return []
    if len(artists) > 1:
        return artists
    return artists[0].split("/")


def get_meta_via_tag(filepath: str) -> tuple[Optional[str], list[str], Optional[str]]:
    "返回 title, artists, comment"
    if not TinyTag.is_supported(filepath):
        return None, [], None
    tag = TinyTag.get(filepath)
    title = tag.title
    if a := tag.artist:
        artists = [a]
        if isinstance(oa := tag.extra.get("other_artists"), list):
            artists += oa
    else:
        artists = []
    comment = tag.comment
    return title, artists, comment


def get_meta_via_163key(key: str) -> tuple[Optional[str], list, Optional[int]]:
    "返回 title, artists, mid"
    if data := ncmkey.decrypt(key):
        return data["musicName"], [i[0] for i in data["artist"]], data["musicId"]
    return None, [], None


def get_meta_via_filename(fn: str) -> tuple[str, list]:
    if m := re.match(REGEX_TRACK_PREFIX, fn):
        # {track}. {title}
        return fn.removeprefix(m.group(1)), []
    sp = fn.split(" - ", 1)
    if len(sp) == 2:
        # {artists} - {title}
        artist_str, title = sp
        artists = artist_str.split(",")
    else:
        # {title}
        title = sp[0]
        artists = []
    return title, artists


def get_fileinfo(file: str) -> tuple[Optional[str], list[str], Optional[int]]:
    """
    返回元组
    Title(str), artists(list), music_id(int)

    未知的用 None 或 []占位
    """
    title = None
    artists: list[str] = []

    title, artists, comm = get_meta_via_tag(file)
    if comm:
        comm = comm.strip()
        if comm.startswith("163 key"):
            try:
                return get_meta_via_163key(comm)
            except Exception as e:
                logging.warning("error while parsing 163 key: %s", e)
    if title:
        return title, artists, None
    title, artists = get_meta_via_filename(file)
    return title, artists, None


def save_lyrics(filename: str, path: str, lrc: str) -> None:
    # 不需要后缀名
    filename += ".lrc"
    file = os.path.join(path, filename)
    with open(file, "w+", encoding="utf-8", errors="replace") as f:
        f.write(lrc)
    logging.info('Lyrics file saved to "%s" successfully ', file)


def generate_filename(
    title: str,
    artists: list[str],
    filename_template: str = "{artists} - {title}",
    artist_sep: str = ",",
):
    return replace_char(
        normalize(
            filename_template.format(artists=artist_sep.join(artists), title=title)
        )
    )

def walk_topfolder(path: str):
    # 返回的数据结构与os.walk()保持一致
    dirs = os.listdir(path)
    files = []
    folders = []
    for d in dirs:
        if os.path.isfile(os.path.join(path, d)):
            files.append(d)
        elif os.path.isdir(os.path.join(path, d)):
            folders.append(d)
    yield path, folders, files
