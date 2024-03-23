import os
import re
import sys
import logging
import tkinter as tk
from tkinter import filedialog
import unicodedata
import typing

from tinytag import TinyTag
from bs4 import BeautifulSoup as BS
import colorama
from retry import retry

import ncmapis
import ncmkey
from lrchandler import combine as combine_lrc
import requester as reqer

version = "2.2.1"

config = {
    "version": version,
    "output": {
        "encoding": "utf-8",
        "filename": "{artists} - {title}",
        "artist_separator": ",",
    },
    "input": {
        "filename": "{artists} - {title}",
        "artist_separator": ",",
    },
    "retry_time": 3,
}

root_window = tk.Tk()
root_window.withdraw()
colorama.init(autoreset=True)
valid_music_extensions = [
    ".m4a",
    ".mp3",
    ".flac",
    ".alac",
    ".aac",
    ".aif",
    ".wma",
    ".wav",
    ".ogg",
    ".opus",
]


def normalize(text: str) -> str:
    return replace_char(unicodedata.normalize("NFKC", text).strip())


def replace_char(text: str) -> str:
    repChr = {
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
    for t in list(repChr.keys()):
        text = text.replace(t, repChr[t])
    return text


def get_tag(file: str) -> dict:
    return TinyTag.get(file)._as_dict()


def parse_filename(fn: str) -> tuple:
    fn = fn.split(" - ", 1)
    if len(fn) == 2:
        artists, title = fn
        artists = artists.split(",")
    else:
        title = fn[0]
        artists = []
    return title, artists


def get_fileinfo(file: str) -> typing.Tuple[str, typing.List[str], int]:
    """
    返回元组
    Title(str), artists(list), music_id(int)

    未知的用 None 或 []占位
    """
    title = None
    artists = []
    music_id = None
    # music tag
    try:
        tags = get_tag(file)
    except Exception as e:
        logging.error("Error while extracting music tag from {}: {}".format(file, e))
    else:
        # 163 key
        if tags["comment"]:
            comment = tags["comment"].strip()
            if comment.startswith("163 key") and len(comment) > 50:
                key = comment[22:]
                try:
                    data = ncmkey.parse(key)
                except Exception as e:
                    logging.error("Error while trying parsing 163 key: " + str(e))
                else:
                    logging.debug("Data from 163 key: " + str(data))
                    if "musicName" in data:
                        title = data["musicName"]
                    if "artist" in data:
                        artists = [i[0] for i in data["artist"]]
                    if "musicId" in data:
                        music_id = data["musicId"]
            if tags["title"] and not title:
                title = tags["title"]
            if tags["artist"] and not artists:
                artists = re.split(r'[/\0]', tags["artist"])
    # filename
    t, a = parse_filename(os.path.splitext(os.path.split(file)[1])[0])
    if t and not title:
        title = t
    if a and not artists:
        artists = a
    return title, artists, music_id


def save_lyrics(filename: str, path: str, lrc: str) -> None:
    # 不需要后缀名
    filename += ".lrc"
    file = os.path.join(path, filename)
    with open(file, "w+", encoding="utf-8", errors="replace") as f:
        f.write(lrc)
    logging.info('Lyrics file saved to "{}" successfully '.format(file))


generate_filename = lambda title, artists: replace_char(
    normalize(config["output"]["filename"].format(
        artists=config["output"]["artist_separator"].join(artists), title=title
    ))
)
# 不含后缀名


# @ncmapis.auto_retry()
@retry(exceptions=(PermissionError), tries=3, delay=0.5)
def download_lyrics(
    mid: int,
    topath: str = None,
    version: typing.Literal["ask","original","translated","both","merge"] = "original",
    info: dict = None,
    lrcs: dict = None,
) -> typing.Literal[0,1,2]:
    """
    info 是预处理信息, 从 ncmapis.get_info() 获取的数据, 为的是避免重复请求

    lrcs 同上, 从 ncmapis.get_lyrics() 获取的数据

    version 决定下载的歌词的版本
    - 为 ask 且 有歌词翻译 时, 会进行询问
    - 为 original 时, 下载原歌词
    - 为 translated 时, 下载翻译过的歌词
    - 为 both 时, 下载两个版本的歌词 并添加文件名后缀
    - 为 merge 时, 先下载两个版本的歌词 再用 combine_lrc 拼起来 删掉原文件

    但是 若是没能获取到翻译歌词, version 会被自动改成 original

    返回成功下载的歌词数量, 只可能为: 0, 1, 2 (Merge 视为 2)
    """
    # 收集信息
    version = version.strip().lower()
    if info:
        pass
    else:
        info = ncmapis.get_info(mid)
    if lrcs:
        lrc_orig, lrc_trans = lrcs
    else:
        lrc_orig, lrc_trans = ncmapis.get_lyrics(mid)
    #
    print(
        "Music info: [",
        colorama.Fore.CYAN + info["title"],
        "] ID=",
        colorama.Fore.GREEN + str(info["mid"]),
        sep="",
    )
    if not lrc_orig:
        logging.warning("Music ID {} has no lyrics".format(mid))
        return 0
    if not topath:
        topath = filedialog.askdirectory(title="Specify an output path")
        if not topath:
            print(colorama.Fore.RED + "Unspecified output path, operation terminated.")
            return 0
    if version != "original" and not lrc_trans:
        version = "original"
        logging.warning("There's only original lyrics to download: mID {}".format(mid))
    if version == "ask" and lrc_trans:
        version = ask_for_version()
    #
    if version == "original":
        filename = generate_filename(title=info["title"], artists=info["artists"])
        save_lyrics(filename, topath, lrc_orig)
        return 1
    elif version == "translated":
        filename = generate_filename(title=info["title"], artists=info["artists"])
        save_lyrics(filename, topath, lrc_trans)
        return 1
    elif version == "both":
        filename = generate_filename(title=info["title"], artists=info["artists"])
        save_lyrics(filename + ".original", topath, lrc_orig)
        save_lyrics(filename + ".translated", topath, lrc_trans)
        return 2
    elif version == "merge":
        filename = generate_filename(title=info["title"], artists=info["artists"])
        save_lyrics(filename + ".original", topath, lrc_orig)
        save_lyrics(filename + ".translated", topath, lrc_trans)
        fm = os.path.join(topath, filename + ".original.lrc")
        fs = os.path.join(topath, filename + ".translated.lrc")
        with open(os.path.join(topath, filename + ".lrc"), 'w+', encoding='utf-8') as f:
            f.write(combine_lrc(lrc_main=fm, lrc_sub=fs))
        os.remove(fm)
        os.remove(fs)
        return 2


# https://github.com/amjith/fuzzyfinder/
def fuzzy_match(string, collection, accessor=lambda x: x, sort_results=True):
    suggestions = []
    string = str(string) if not isinstance(string, str) else string
    pat = ".*?".join(map(re.escape, string))
    pat = "(?=({0}))".format(pat)  # lookahead regex to manage overlapping matches
    regex = re.compile(pat, re.IGNORECASE)
    for item in collection:
        r = list(regex.finditer(accessor(item)))
        if r:
            best = min(r, key=lambda x: len(x.group(1)))  # find shortest match
            suggestions.append((len(best.group(1)), best.start(), accessor(item), item))
    if sort_results:
        return (z[-1] for z in sorted(suggestions))
    else:
        return (z[-1] for z in sorted(suggestions, key=lambda x: x[:2]))


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


def menu(text: str, option_table: dict, dist_case: bool = True) -> str:
    """
    option_table:
    { user_input(str): option_text(str) }
    """
    print("")
    possi_input = list(option_table.keys())
    if not dist_case:
        possi_input = [i.lower() for i in possi_input]
    print(text)
    for k, v in option_table.items():
        print(" (", colorama.Fore.CYAN + k, ")", v, sep="")
    while True:
        choice = input("Choice:").strip()
        if not dist_case:
            choice = choice.lower()
        if choice in possi_input:
            return choice
        else:
            print(colorama.Fore.RED + "Unexpected input. Make choice again.")


ask_for_version = lambda: {
    "1": "original",
    "2": "translated",
    "3": "both",
    "4": "merge",
}[
    menu(
        "Choose lyrics version.",
        {
            "1": "Original",
            "2": "Translated",
            "3": "Both (Version Suffix will be added)",
            "4": "Merge (A double-languaged lrc file will be created)",
        },
    )
]


def extract_id(text: str) -> typing.Tuple[int, typing.Literal["music_id", "album_id", "unknown"]]:
    i = re.findall(r"[^a-zA-Z]id\=([0-9]+)", text, flags=re.I)
    if i and "/song?" in text:
        return int(i[0]), "music_id"
    if i and "/album?" in text:
        return int(i[0]), "album_id"
    return -1, "unknown"


def download_via_music_id() -> None:
    source = input("Music ID or URL:").strip()
    if source.isdigit():
        music_id = int(source)
    else:
        id_, type_ = extract_id(source)
        if type_ == "music_id":
            music_id = id_
        else:
            print(colorama.Fore.RED + "Unrecognized Input:", source)
            return
    if music_id > 0:
        # topath = filedialog.askdirectory(title='Specify an output path')
        download_lyrics(music_id, topath=None, version="ask")
        print("Done!")
    else:
        print(colorama.Fore + "Invalid Music ID: %s" % music_id)


def download_via_album_id() -> None:
    source = input("Album ID or URL:").strip()
    if source.isdigit():
        album_id = int(source)
    else:
        id_, type_ = extract_id(source)
        if type_ == "album_id":
            album_id = id_
        else:
            print(colorama.Fore.RED + "Unrecognized Input:", source)
            return
    if album_id > 0:
        topath = filedialog.askdirectory(title="Specify an output path")
        if topath:
            print("Specified output:", topath)
            data = ncmapis.get_album(album_id)
            print(
                "Album Info: [",
                colorama.Fore.CYAN + data["title"],
                "] ID=",
                colorama.Fore.GREEN + str(data["aid"]),
                sep="",
            )
            default_version = ask_for_version()
            for music in data["music_list"]:
                download_lyrics(
                    music["mid"], topath=topath, version=default_version, info=music
                )
            print("Done!")
        else:
            print(colorama.Fore.RED + "Unspecified output path, operation terminated.")
    else:
        print(colorama.Fore + "Invalid Album ID: %s" % album_id)


def match_music(root: str, file: str) -> typing.Union[typing.Tuple[int, typing.Union[dict, None]], None]:
    """
    返回 一个元组 或 None

    元组: (music_id(int), info(dict))

    元组中的 info 可能为 None
    """
    base, extension = os.path.splitext(file)
    if extension.lower() in valid_music_extensions:
        title, artists, musicid = get_fileinfo(os.path.join(root, file))
        if musicid:
            print(
                'File "',
                colorama.Fore.CYAN + file,
                '" is [',
                colorama.Fore.CYAN + title,
                "] ID=",
                colorama.Fore.GREEN + str(musicid),
                sep="",
            )
            return (musicid, {"title": title, "artists": artists, "mid": musicid})
        else:
            if artists:
                data = ncmapis.search_music(title, *artists)
            else:
                data = ncmapis.search_music(title)
            if not data:
                print(
                    colorama.Fore.YELLOW + 'File "{}" has no match result.'.format(file)
                )
                return None
            titles_to_match = [i["title"] for i in data]
            match_res = fuzzy_match(title, titles_to_match)
            try:
                matched_obj = data[titles_to_match.index(next(match_res))]
                print(
                    'File "',
                    colorama.Fore.CYAN + file,
                    '" matched [',
                    colorama.Fore.CYAN + matched_obj["title"],
                    "] ID=",
                    colorama.Fore.GREEN + str(matched_obj["mid"]),
                    sep="",
                )
                return (matched_obj["mid"], matched_obj)
            except StopIteration:
                print(
                    colorama.Fore.YELLOW + 'File "{}" has no match result.'.format(file)
                )
                return None
    else:
        print(
            colorama.Fore.YELLOW + 'File "{}" is not supported music file.'.format(file)
        )
        return None


def download_via_scanning() -> None:
    path = filedialog.askdirectory(title="Specify a folder to scan")
    if not path:
        print(colorama.Fore.RED + "Unspecified scanning path, operation terminated.")
        return
    counter = 0
    default_version = ask_for_version()
    for root, folders, files in {"1": walk_topfolder, "2": os.walk}[
        menu("Choose scanning depth.", {"1": "Top folder only", "2": "All"})
    ](path):
        for file in files:
            match_res = match_music(root, file)
            counter += 1
            if match_res:
                mid, info = match_res
                download_lyrics(mid, root, version=default_version, info=info)
            else:
                continue
    print("Tried handling {} file(s) in total.".format(counter))


def download_via_specifying() -> None:
    files = filedialog.askopenfilenames(title="Choose some files to match.")  #
    if not files:
        print(colorama.Fore.RED + "No specified file, operation terminated.")
        return
    default_version = ask_for_version()
    print("{} file(s) will be checked soon.".format(len(files)))
    counter = 0
    for fullpath in files:
        root, file = os.path.split(fullpath)
        match_res = match_music(root, file)
        counter += 1
        if match_res:
            mid, info = match_res
            download_lyrics(mid, root, version=default_version, info=info)
        else:
            continue
    print("Tried handling {} file(s) in total.".format(counter))


def main() -> None:
    global config
    print("Welcome to", colorama.Fore.LIGHTRED_EX + "CMLD.")
    print(
        "I mean,",
        "(Netease)",
        colorama.Fore.CYAN + "Cloud Music Lyrics Downloader",
        colorama.Fore.LIGHTBLACK_EX + "XD",
    )
    print("\nCurrent Version:", version, "\n")
    while True:
        choice = menu(
            "Choose one option to get started.",
            {
                "1": "Download lyrics via Music ID.",
                "2": "Download lyrics of each music in an album via Album ID.",
                "3": "Automatically scan local folder and download lyrics for each music file.",
                "4": "Choose music files in person and download lyrics for them.",
                "Q": "Quit",
                "C": "Config",
            },
            False,
        )
        # print(choice)
        if choice == "1":
            download_via_music_id()
        elif choice == "2":
            download_via_album_id()
        elif choice == "3":
            download_via_scanning()
        elif choice == "4":
            download_via_specifying()
        elif choice == "q":
            sys.exit(0)
        elif choice == "c":
            print("Configuration module is being building, sorry...")


if __name__ == "__main__":
    if "--debug" in sys.argv:
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG,
        )
        print(colorama.Fore.LIGHTBLACK_EX + "-- Debug Mode --")
    main()
