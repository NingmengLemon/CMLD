from http import cookiejar
from urllib import request, parse, error
import os
import re
import sys
import time
import json
import zlib,gzip
import _thread
import hashlib
import math
from io import BytesIO

fake_headers_get = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43',  # noqa
    'Referer':'https://www.bilibili.com/'
}

fake_headers_post = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43'
    }

user_name = os.getlogin()
encodec = 'MBCS'

def _ungzip(data):
    """Decompresses data for Content-Encoding: gzip.
    """
    buffer = BytesIO(data)
    f = gzip.GzipFile(fileobj=buffer)
    return f.read()

def _undeflate(data):
    """Decompresses data for Content-Encoding: deflate.
    (the zlib compression is used.)
    """
    decompressobj = zlib.decompressobj(-zlib.MAX_WBITS)
    return decompressobj.decompress(data)+decompressobj.flush()

def _get_response(url, headers=fake_headers_get):
    opener = request.build_opener()
    if headers:
        response = opener.open(
            request.Request(url, headers=headers), None
        )
    else:
        response = opener.open(url)

    data = response.read()
    if response.info().get('Content-Encoding') == 'gzip':
        data = _ungzip(data)
    elif response.info().get('Content-Encoding') == 'deflate':
        data = _undeflate(data)
    response.data = data
    return response

def get_content(url, headers=fake_headers_get):
    content = _get_response(url, headers=headers).data
    return content

def get_lyrics(mid):
    api = f'https://music.163.com/api/song/lyric?id={str(mid)}&lv=1&kv=1&tv=-1'
    try:
        data = json.loads(get_content(api).decode('utf-8','ignore'))
        if 'lrc' in data:
            lyrics = data['lrc']['lyric']
            if 'tlyric' in data:
                if data['tlyric']['lyric'].strip():
                    lyrics_trans = data['tlyric']['lyric']
                else:
                    lyrics_trans = None
            else:
                lyrics_trans = None
        else:
            lyrics = lyrics_trans = None
    except Exception as e:
        print(str(e))
        lyrics = lyrics_trans = None
    return lyrics,lyrics_trans

def parse_source(source):
    res = None
    try:
        source = int(source)
    except ValueError:
        res = re.findall(r'id\=([0-9]+)',source,flags=re.I)
        if res:
            res = int(res[0])
        else:
            res = None
    else:
        res = source
    return res

if __name__ == '__main__':
    print('Welcome to CMLD!')
    while True:
        mid = input('Input the source:')
        mid = parse_source(mid)
        if mid:
            olrc,tlrc = get_lyrics(mid)
            if olrc and tlrc:
                choice = input('Original ver (1) or Translated ver (2) :').strip()
                if choice == '1':
                    with open('./%s_original.lrc'%mid,'w+',encoding=encodec,errors='ignore') as f:
                        f.write(olrc)
                elif choice == '2':
                    with open('./%s_translated.lrc'%mid,'w+',encoding=encodec,errors='ignore') as f:
                        f.write(tlrc)
                print('Done.')
            elif olrc and not tlrc:
                with open('./%s_original.lrc'%mid,'w+',encoding=encodec,errors='ignore') as f:
                    f.write(olrc)
                print('Done.')
            else:
                print('No lyrics to be downloaded.')
        else:
            pass
        print('')
