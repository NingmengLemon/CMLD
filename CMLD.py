import os
import re
import sys
import time
import json
from io import BytesIO
import winreg
from bs4 import BeautifulSoup as BS
import logging
import requester
import tkinter as tk
from tkinter import filedialog
from functools import wraps

version = '2.1.0'

encoding = 'utf-8'
root_window = tk.Tk()
root_window.withdraw()

def auto_retry(retry_time=3):
    def retry_decorator(func):
        @wraps(func)
        def wrapped(*args,**kwargs):
            _run_counter = 0
            while True:
                _run_counter += 1
                try:
                    return func(*args,**kwargs)
                except Exception as e:
                    print(e)
                    if _run_counter > retry_time:
                        raise e
        return wrapped
    return retry_decorator
    

def get_desktop():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders')
    return winreg.QueryValueEx(key,"Desktop")[0]

desktop = get_desktop()

@auto_retry()
def get_info(mid):
    url = 'https://music.163.com/song?id={mid}'.format(mid=mid)
    bs = BS(requester.get_content_str(url),'html.parser')
    res = {
        'title':bs.find('em',class_='f-ff2').get_text(),
        'artists':[i.get_text() for i in bs.find_all('p',class_='des s-fc4')[0].find_all('a',class_='s-fc7')],
        'album':bs.find_all('p',class_='des s-fc4')[1].find('a',class_='s-fc7').get_text(),
        'album_id':int(bs.find_all('p',class_='des s-fc4')[1].find('a',class_='s-fc7').attrs['href'].split('?id=')[-1]),
        #'subtitle':bs.find('div',class_='subtit f-fs1 f-ff2').get_text(),
        'cover:':bs.find('img',class_='j-img').attrs['data-src']
        }
    return res

@auto_retry()
def get_album(aid):
    url = 'https://music.163.com/album?id={aid}'.format(aid=aid)
    bs = BS(requester.get_content_str(url),'html.parser')
    data = json.loads(bs.find('textarea',id='song-list-pre-data').get_text())
    res = {
        'music_list':[{
            'order':i['no'],
            'title':i['name'],
            'mid':i['id'],
            'artists':[a['name'] for a in i['artists']],
            } for i in data],
        'aid':aid,
        'title':bs.find('h2',class_='f-ff2').get_text(),
        'artists':[i.get_text() for i in bs.find('p',class_='intr').find_all('a',class_='s-fc7')]
        }
    return res

@auto_retry()
def search_music(*kws,limit=10,offset=0):
    url = 'https://music.163.com/api/search/get/?s={}&limit={}&type=1&offset={}'.format('+'.join([requester.parse.quote(kw) for kw in kws]),limit,offset)
    data = json.loads(requester.get_content_str(url))
    if 'songs' in data['result']:
        res = [{
            'mid':i['id'],'title':i['name'],
            'artists':[a['name'] for a in i['artists']],
            'album':i['album']['name'],
            'album_id':i['album']['id']
            #'trans_titles':i['transNames'],
            } for i in data['result']['songs']]
        return res
    else:
        return []

def replace_char(text):
    repChr = {'/':'／','*':'＊',':':'：','\\':'＼','>':'＞',
              '<':'＜','|':'｜','?':'？','"':'＂'}
    for t in list(repChr.keys()):
        text = text.replace(t,repChr[t])
    return text

@auto_retry()
def get_lyrics(mid):
    api = f'https://music.163.com/api/song/lyric?id={str(mid)}&lv=1&kv=1&tv=-1'
    data = json.loads(requester.get_content_str(api))
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
    return lyrics,lyrics_trans

def parse_filename(fn):
    fn = fn.split(' - ',1)
    if len(fn) == 2:
        artists,title = fn
        artists = artists.split(',')
    else:
        title = fn[0]
        artists = []
    return title,artists

@auto_retry()
def download_lyrics(mid,topath,trans=False,info=None,lrcs=None):
    '''info和lrcs是预处理信息, 从信息获取函数获取的源数据, 为的是避免重复请求'''
    if info:
        pass
    else:
        info = get_info(mid)
    if lrcs:
        lrc_orig,lrc_trans = lrcs
    else:
        lrc_orig,lrc_trans = get_lyrics(mid)
    if trans and lrc_trans:
        lrc = lrc_trans
    else:
        lrc = lrc_orig
    if lrc:
        filename = replace_char('{} - {}.lrc'.format(','.join(info['artists']),info['title']))
        with open(os.path.join(topath,filename),'w+',encoding=encoding,errors='ignore') as f:
            f.write(lrc)
        print('Save',filename,'>>',topath)
    else:
        print('Music ID',mid,'has no lyrics.')

#https://github.com/amjith/fuzzyfinder/
def fuzzy_match(string, collection, accessor=lambda x: x, sort_results=True):
    suggestions = []
    string = str(string) if not isinstance(string, str) else string
    pat = '.*?'.join(map(re.escape, string))
    pat = '(?=({0}))'.format(pat)   # lookahead regex to manage overlapping matches
    regex = re.compile(pat, re.IGNORECASE)
    for item in collection:
        r = list(regex.finditer(accessor(item)))
        if r:
            best = min(r, key=lambda x: len(x.group(1)))   # find shortest match
            suggestions.append((len(best.group(1)), best.start(), accessor(item), item))
    if sort_results:
        return (z[-1] for z in sorted(suggestions))
    else:
        return (z[-1] for z in sorted(suggestions, key=lambda x: x[:2]))

def walk_topfolder(path):
    dirs = os.listdir(path)
    files = []
    folders = []
    for d in dirs:
        if os.path.isfile(os.path.join(path,d)):
            files.append(d)
        elif os.path.isdir(os.path.join(path,d)):
            folders.append(d)
    yield path,folders,files
            

def main():
    global encoding
    print('Welcome to CMLD.')
    print('Current Version:',version)
    while True:
        choice = input('\nChoose one option to start.'\
                       '\n (1)Download lyrics via music id.'\
                       '\n (2)Parse album via album id and download lyrics of each music.'\
                       '\n (3)Scan local folder and download lyrics of each music file according to their filename.'\
                       '\nChoice:').strip()
        if choice == '1':
            source = input('Music ID or Url:').strip()
            if source.isdigit():
                music_id = int(source)
            else:
                i = re.findall(r'[^a-zA-Z]id\=([0-9]+)',source,flags=re.I)
                if i and '/song?' in source:
                    music_id = int(i[0])
                else:
                    music_id = None
            if music_id:
                lrc_orig,lrc_trans = get_lyrics(music_id)
                if lrc_orig and lrc_trans:
                    trans = input('Original version (0) or Translated version (1):').strip()
                    if trans == '1':
                        download_lyrics(music_id,desktop,trans=True,lrcs=(lrc_orig,lrc_trans))
                    else:
                        download_lyrics(music_id,desktop,trans=False,lrcs=(lrc_orig,lrc_trans))
                elif lrc_orig and not lrc_trans:
                    download_lyrics(music_id,desktop,trans=False,lrcs=(lrc_orig,lrc_trans))
                else:
                    print('No lyrics to download.')
            else:
                print('No music id to extract.')
        elif choice == '2':
            source = input('Album ID or Url:')
            if source.isdigit():
                album_id = int(source)
            else:
                i = re.findall(r'[^a-zA-Z]id\=([0-9]+)',source,flags=re.I)
                if i and '/album?' in source:
                    album_id = int(i[0])
                else:
                    album_id = None
            if album_id:
                trans = input('Original version (0) or Translated version (1):').strip()
                if trans == '1':
                    trans = True
                else:
                    trans = False
                topath = filedialog.askdirectory(title='Choose Output Path')
                if topath:
                    print('Working...')
                    album = get_album(album_id)
                    for item in album['music_list']:
                        download_lyrics(item['mid'],topath=topath,trans=trans)
                else:
                    print('No path to release files.')
            else:
                print('No album id to extract.')
        elif choice == '3':
            match_mode = input('Fuzzy match (0) or Complete match (1):').strip() #匹配模式
            if match_mode == '1':
                fuzzy = False
            else:
                fuzzy = True
            trans = input('Original version (0) or Translated version (1):').strip() #是否翻译
            if trans == '1':
                trans = True
            else:
                trans = False
            toponly = input('Top folder only (0) or All file tree (1)').strip()
            if toponly == '1':
                toponly = False
            else:
                toponly = True
            workdir = filedialog.askdirectory(title='Choose Path to Scan') #
            if workdir:
                print('Working...')
                loop_counter = 0
                for root,folders,files in {False:os.walk,True:walk_topfolder}[toponly](workdir):
                    for file in files:
                        loop_counter += 1
                        base,extension = os.path.splitext(file)
                        if extension.lower() in ['.m4a','.mp3','.flac','.aac','.ape','.wma']:
                            title,artists = parse_filename(base)
                            data = search_music(title,*artists)
                            if not data:
                                print('File "{}" has no match result.'.format(file))
                                continue
                            if fuzzy:
                                titles_to_match = [i['title'] for i in data]
                                match_res = fuzzy_match(title,titles_to_match)
                                try:
                                    matched_obj = data[titles_to_match.index(next(match_res))]
                                    print('File "{}" matched music "{}"(id{}).'.format(file,matched_obj['title'],matched_obj['mid']))
                                    download_lyrics(matched_obj['mid'],root,trans=trans,info=matched_obj) #因为键的命名方法一致, 所以可以直接传入
                                except StopIteration:
                                    print('File "{}" has no match result.'.format(file))
                            else:
                                for obj in data:
                                    if obj['title'] == title and sum([(i in obj['artists']) for i in artists]) == len(artists):
                                        print('File "{}" matched music "{}"(id{}).'.format(file,obj['title'],obj['mid']))
                                        download_lyrics(matched_obj['mid'],root,trans=trans,info=obj)
                                        break
                                    else:
                                        print('File "{}" has no match result.'.format(file))
                        else:
                            continue
            else:
                print('No path to scan file.')
        elif choice.lower() == 'cls':
            os.system('cls')
        elif choice.lower() == 'config':
            option = input('Config Menu'\
                           ' (1)Encoding'\
                           'Choice:').strip().lower()
            if option == '1':
                print('Current Encoding:',encoding)
                new_enc = input('New Encoding:').strip().lower()
                if new_enc:
                    encoding = new_enc
            
            
if __name__ == '__main__':
    if '-debug' in sys.argv:
        logging.basicConfig(format='[%(asctime)s][%(levelname)s]%(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.DEBUG
                            )
        print('-Debug Mode-')
    main()
