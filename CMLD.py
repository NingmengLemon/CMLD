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
import winreg

def get_desktop():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    return winreg.QueryValueEx(key,"Desktop")[0]

fake_headers_get = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43',  # noqa
}

fake_headers_post = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43'
    }

user_name = os.getlogin()
desktop_path = get_desktop()
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

def get_info(mid):
    url = 'https://music.163.com/song?id={mid}'.format(mid=mid)
    data = get_content(url).decode('utf-8','ignore')
    res = {}
    try:
        res['album'] = re.findall(r'\<meta property\=\"og\:music\:album\" content=\"(.+)\" *\/\>',data)[0]
        res['title'] = re.findall(r'\<meta property\=\"og\:title\" content=\"(.+)\" *\/\>',data)[0]
        res['image'] = re.findall(r'\<meta property\=\"og\:image\" content=\"(.+)\" *\/\>',data)[0]
        res['url'] = url
        res['artist'] = []
        tmp = re.findall(r'\<p class\=\"des s\-fc4\"\>歌手：(.+)\<\/p\>',data)[0].split(' / ')
        for t in tmp:
            sp = re.findall(r'\<a class\=\"s\-fc7\" href\=\"\/artist\?id\=[0-9]+\" *>(.+)\<\/a\>',t)
            if sp:
                res['artist'].append(sp[0])
    except IndexError:
        print('Match ERROR: Music info not found.')
        res = None
    except Exception as e:
        print('Unexpected ERROR:',str(e))
        res = None
    return res

def replace_char(text):
    repChr = {'/':'／','*':'＊',':':'：','\\':'＼','>':'＞',
              '<':'＜','|':'｜','?':'？','"':'＂'}
    for t in list(repChr.keys()):
        text = text.replace(t,repChr[t])
    return text

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
        res = re.findall(r'[^a-zA-Z0-9]id\=([0-9]+)',source,flags=re.I)
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
            info = get_info(mid)
            if info:
                file = os.path.join(desktop_path,replace_char('{0} - {1}.lrc'.format(','.join(info['artist']),info['title'])))
            else:
                file = os.path.join(desktop_path,'{}.lrc'.format(mid))
            olrc,tlrc = get_lyrics(mid)
            if olrc and tlrc:
                choice = input('Original ver (1) or Translated ver (2) :').strip()
                if choice == '1' or not choice:
                    with open(file,'w+',encoding=encodec,errors='ignore') as f:
                        f.write(olrc)
                elif choice == '2':
                    with open(file,'w+',encoding=encodec,errors='ignore') as f:
                        f.write(tlrc)
                print('Lrc file has been saved to Desktop with encoding %s.'%encodec)
            elif olrc and not tlrc:
                with open(file,'w+',encoding=encodec,errors='ignore') as f:
                    f.write(olrc)
                print('Lrc file has been saved to Desktop with encoding %s.'%encodec)
            else:
                print('No lyrics to be downloaded.')
        else:
            pass
        print('')
