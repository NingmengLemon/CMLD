from urllib import request, parse, error
import json
import zlib, gzip
import os
import re
import sys
from io import BytesIO
import logging
import copy
import time

import brotli

user_name = os.getlogin()

fake_headers_get = {
    "Host": "music.163.com",
    "Referer": "https://music.163.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
}

fake_headers_post = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43"
}

timeout = 15


def _replaceChr(text:str)->str:
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


def _ungzip(data:bytes)->bytes:
    """Decompresses data for Content-Encoding: gzip."""
    buffer = BytesIO(data)
    f = gzip.GzipFile(fileobj=buffer)
    return f.read()


def _undeflate(data:bytes)->bytes:
    """Decompresses data for Content-Encoding: deflate.
    (the zlib compression is used.)
    """
    decompressobj = zlib.decompressobj(-zlib.MAX_WBITS)
    return decompressobj.decompress(data) + decompressobj.flush()


def _unbrotli(data:bytes)->bytes:
    return brotli.decompress(data)


def _dict_to_headers(dict_to_conv:dict)->list:
    keys = list(dict_to_conv.keys())
    values = list(dict_to_conv.values())
    res = []
    for i in range(len(keys)):
        res.append((keys[i], values[i]))
    return res


def _get(url:str, headers:dict=fake_headers_get):
    opener = request.build_opener()

    if headers:
        response = opener.open(
            request.Request(url, headers=headers), None, timeout=timeout
        )
    else:
        response = opener.open(url, timeout=timeout)

    data = response.read()
    if response.info().get("Content-Encoding") == "gzip":
        data = _ungzip(data)
    elif response.info().get("Content-Encoding") == "deflate":
        data = _undeflate(data)
    elif response.info().get("Content-Encoding") == "br":
        data = _unbrotli(data)
    response.data = data
    logging.debug("Get: " + url)
    return response


def _post(url:str, data:dict, headers:dict=fake_headers_post):
    opener = request.build_opener()
    params = parse.urlencode(data).encode()
    if headers:
        response = opener.open(
            request.Request(url, data=params, headers=headers), timeout=timeout
        )
    else:
        response = opener.open(request.Request(url, data=params), timeout=timeout)
    data = response.read()
    if response.info().get("Content-Encoding") == "gzip":
        data = _ungzip(data)
    elif response.info().get("Content-Encoding") == "deflate":
        data = _undeflate(data)
    elif response.info().get("Content-Encoding") == "br":
        data = _unbrotli(data)
    response.data = data
    logging.debug("Post: {}".format(url))
    return response


def post_str(url:str, data:dict, headers:dict=fake_headers_post, encoding:str="utf-8")->str:
    response = _post(url, data, headers)
    return response.data.decode(encoding, "ignore")


def post_bytes(url:str, data:dict, headers:dict=fake_headers_post)->bytes:
    response = _post(url, data, headers)
    return response.data


def get_str(url:str, encoding:str="utf-8", headers:dict=fake_headers_get)->str:
    content = _get(url, headers=headers).data
    data = content.decode(encoding, "ignore")
    return data


def get_bytes(url:str, headers:dict=fake_headers_get)->bytes:
    content = _get(url, headers=headers).data
    return content


def get_redirect_url(url:str, headers:dict=fake_headers_get)->str:
    return request.urlopen(request.Request(url, headers=headers), None).geturl()


# Download Operation
def download_common(url:str, tofile:str, progressfunc=None, headers:dict=fake_headers_get)->None:
    opener = request.build_opener()
    opener.addheaders = _dict_to_headers(headers)
    request.install_opener(opener)
    request.urlretrieve(url, tofile, progressfunc)
