import os
import re
import sys
import logging
import tkinter as tk
from tkinter import filedialog
from typing import Literal, Optional, TypeAlias, Any
import argparse

import colorama
from retry import retry
from tinytag import TinyTag

import ncmapis
from lrchandler import combine as combine_lrc
from core import (
    generate_filename,
    save_lyrics,
    get_fileinfo,
    walk_topfolder,
    fuzzy_match,
)

VERSION = "2.3.0"

LYRIC_VERSIONS = ["ask", "original", "translated", "both", "merge"]
LyricVersionType: TypeAlias = Literal["ask", "original", "translated", "both", "merge"]

config: dict[str, Any] = {
    "version": VERSION,
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

VALID_MUSIC_EXTENSIONS = TinyTag.SUPPORTED_FILE_EXTENSIONS

root_window: Optional[tk.Tk] = None


def get_hidden_window():
    window = tk.Tk()
    window.withdraw()
    return window


def init_root_window():
    global root_window
    if not root_window:
        root_window = get_hidden_window()


@retry(exceptions=(PermissionError), tries=3, delay=0.5)
def download_lyrics(
    mid: int,
    topath: Optional[str] = None,
    version: LyricVersionType = "original",
    info: Optional[dict] = None,
    lrcs: Optional[tuple[Optional[str], Optional[str]]] = None,
) -> Literal[0, 1, 2]:
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
    if info is None:
        info = ncmapis.get_info(mid)
    if lrcs is None:
        lrc_orig, lrc_trans = ncmapis.get_lyrics(mid)
    else:
        lrc_orig, lrc_trans = lrcs
    #
    print(
        "Music info: [",
        colorama.Fore.CYAN + info["title"],
        "] ID=",
        colorama.Fore.GREEN + str(info["mid"]),
        sep="",
    )
    if not lrc_orig:
        logging.warning("Music ID %s has no lyrics", mid)
        return 0
    if not topath:
        topath = filedialog.askdirectory(
            title="Specify an output path", parent=root_window
        )
        if not topath:
            print(colorama.Fore.RED + "Unspecified output path, operation terminated.")
            return 0
    if version != "original" and not lrc_trans:
        version = "original"
        logging.warning("There's only original lyrics to download: mID %s", mid)
    if version == "ask" and lrc_trans:
        version = ask_for_version()
    #
    if version == "original":
        filename = generate_filename(
            title=info["title"],
            artists=info["artists"],
            filename_template=config["output"]["filename"],
            artist_sep=config["output"]["artist_separator"],
        )
        save_lyrics(filename, topath, lrc_orig)
        return 1
    elif version == "translated":
        filename = generate_filename(
            title=info["title"],
            artists=info["artists"],
            filename_template=config["output"]["filename"],
            artist_sep=config["output"]["artist_separator"],
        )
        save_lyrics(filename, topath, lrc_trans)
        return 1
    elif version == "both":
        filename = generate_filename(
            title=info["title"],
            artists=info["artists"],
            filename_template=config["output"]["filename"],
            artist_sep=config["output"]["artist_separator"],
        )
        save_lyrics(filename + ".original", topath, lrc_orig)
        save_lyrics(filename + ".translated", topath, lrc_trans)
        return 2
    elif version == "merge":
        filename = generate_filename(
            title=info["title"],
            artists=info["artists"],
            filename_template=config["output"]["filename"],
            artist_sep=config["output"]["artist_separator"],
        )
        save_lyrics(filename + ".original", topath, lrc_orig)
        save_lyrics(filename + ".translated", topath, lrc_trans)
        fm = os.path.join(topath, filename + ".original.lrc")
        fs = os.path.join(topath, filename + ".translated.lrc")
        with open(os.path.join(topath, filename + ".lrc"), "w+", encoding="utf-8") as f:
            f.write(combine_lrc(lrc_main=fm, lrc_sub=fs))
        os.remove(fm)
        os.remove(fs)
        return 2
    return 0


def menu(text: str, option_table: dict[str, str], dist_case: bool = True) -> str:
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


def ask_for_version() -> LyricVersionType:
    return {
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


def extract_id(
    text: str,
) -> tuple[int, Literal["music_id", "album_id", "unknown"]]:
    i = re.findall(r"[^a-zA-Z]id\=([0-9]+)", text, flags=re.I)
    if i and "/song?" in text:
        return int(i[0]), "music_id"
    if i and "/album?" in text:
        return int(i[0]), "album_id"
    return -1, "unknown"


def download_via_music_id(
    source: Optional[str] = None,
    version: LyricVersionType = "ask",
    topath: Optional[str] = None,
) -> None:
    if not source:
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
        download_lyrics(music_id, topath=topath, version=version)
        print("Done!")
    else:
        print(colorama.Fore + "Invalid Music ID: %s" % music_id)


def download_via_album_id(
    source: Optional[str] = None,
    default_version: LyricVersionType = "ask",
    topath: Optional[str] = None,
) -> None:
    if not source:
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
    if album_id <= 0:
        print(colorama.Fore + "Invalid Album ID: %s" % album_id)
        return
    if not topath:
        topath = filedialog.askdirectory(
            title="Specify an output path", parent=root_window
        )
    if not topath:
        print(colorama.Fore.RED + "Unspecified output path, operation terminated.")
        return
    print("Specified output:", topath)
    data = ncmapis.get_album(album_id)
    print(
        "Album Info: [",
        colorama.Fore.CYAN + data["title"],
        "] ID=",
        colorama.Fore.GREEN + str(data["aid"]),
        sep="",
    )
    if default_version == "ask":
        default_version = ask_for_version()
    for music in data["music_list"]:
        download_lyrics(
            music["mid"], topath=topath, version=default_version, info=music
        )
    print("Done!")


def match_music(root: str, file: str) -> Optional[tuple[int, Optional[dict]]]:
    """
    返回 一个元组 或 None

    元组: (music_id(int), info(dict))

    元组中的 info 可能为 None
    """
    _, extension = os.path.splitext(file)
    if extension.lower() in VALID_MUSIC_EXTENSIONS:
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


def download_via_scanning(
    path: Optional[str] = None,
    default_version: LyricVersionType = "ask",
    top_only: Optional[bool] = None,
) -> None:
    if not path:
        path = filedialog.askdirectory(
            title="Specify a folder to scan", parent=root_window
        )
    if not path:
        print(colorama.Fore.RED + "Unspecified scanning path, operation terminated.")
        return
    counter = 0
    if default_version == "ask":
        default_version = ask_for_version()
    if top_only is None:
        walk = {"1": walk_topfolder, "2": os.walk}[
            menu("Choose scanning depth.", {"1": "Top folder only", "2": "All"})
        ]
    elif top_only:
        walk = walk_topfolder
    else:
        walk = os.walk
    for root, _, files in walk(path):
        for file in files:
            match_res = match_music(root, file)
            counter += 1
            if match_res:
                mid, info = match_res
                download_lyrics(mid, root, version=default_version, info=info)
            else:
                continue
    print("Tried handling {} file(s) in total.".format(counter))


def download_via_specifying(
    files: Optional[list[str]] = None, default_version: LyricVersionType = "ask"
) -> None:
    if not files:
        files = filedialog.askopenfilenames(
            title="Choose some files to match.", parent=root_window
        )
    if not files:
        print(colorama.Fore.RED + "No specified file, operation terminated.")
        return
    if default_version == "ask":
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


def app() -> None:
    # global config
    init_root_window()
    print("Welcome to", colorama.Fore.LIGHTRED_EX + "CMLD.")
    print(
        "I mean,",
        "(Netease)",
        colorama.Fore.CYAN + "Cloud Music Lyrics Downloader",
        colorama.Fore.LIGHTBLACK_EX + "XD",
    )
    print("\nCurrent Version:", VERSION, "\n")
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
            print("Configuration module is under building, sorry ww")


def app_noui(args: argparse.Namespace):
    source: str = args.source
    if os.path.isfile(source):
        # single file
        download_via_specifying([source], args.version)
        return
    if os.path.isdir(source):
        # folder
        download_via_scanning(
            source, default_version=args.version, top_only=args.toponly
        )
        return
    if os.path.islink(source):
        print("symbol link not supported :(")
        return
    _, itype = extract_id(source)
    if itype == "album_id":
        # album
        download_via_album_id(source, default_version=args.version, topath=args.saveto)
        return
    elif itype == "music_id":
        # single music
        download_via_music_id(source, version=args.version, topath=args.saveto)
        return
    else:
        # ?
        print("unknown source ww")
        return


if __name__ == "__main__":
    colorama.init(autoreset=True)
    app()
