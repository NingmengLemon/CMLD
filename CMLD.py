import logging
import argparse
import sys

import colorama

from app import app, app_noui, LYRIC_VERSIONS, VERSION


def main():
    parser = argparse.ArgumentParser(
        prog="CMLD",
        description="A simple (Netease) Cloudmusic Lyrics Downloader",
        usage='''CMLD [source] [options]''',
    )
    parser.add_argument("source", nargs="?", type=str, help="source to handle, a file / folder / url or nothing")
    parser.add_argument("--debug", action="store_true", help="enable debug")
    parser.add_argument(
        "--version",
        "-v",
        choices=LYRIC_VERSIONS,
        default="ask",
        help="lyric version to download",
    )
    parser.add_argument(
        "--saveto",
        "-s",
        type=str,
        required=False,
        help="folder to save lyrics, useful when give a path",
    )
    parser.add_argument(
        "--about", action="store_true", help="print about info and quit"
    )
    parser.add_argument(
        "--toponly",
        action="store_true",
        help="only scan top folder, useful when give a path to folder",
    )

    args = parser.parse_args()
    if args.about:
        print("CMLD", f"v{VERSION},", "by", "LemonyNingmeng")
        return
    if args.debug:
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG,
        )
        print(colorama.Fore.LIGHTBLACK_EX + "-- Debug Mode --")
        print("args:", vars(args))
    if args.source is None:
        app()
    else:
        app_noui(args)
    return


if __name__ == "__main__":
    colorama.init(autoreset=True)
    main()
    sys.exit(0)
