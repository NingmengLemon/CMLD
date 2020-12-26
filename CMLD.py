import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
from tkinter import scrolledtext
from urllib import request,parse
import json,gzip,os,re
from sys import exit

version = '1.1.0.20201213_beta'
config = {'official_api':False}
repChr = {'/':'／',
          '*':'＊',
          ':':'：',
          '\\':'＼',
          '>':'＞',
          '<':'＜',
          '|':'｜',
          '?':'？'}

def getData(url,et=5):
    try:
        if url[:8] != "https://":
            if url[:7] != "http://":
                url = "https://" + url
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1"
            }
        dict = {}
        data = bytes(parse.urlencode(dict),encoding="utf-8")
        req = request.Request(url=url,data=data,headers=headers,method="GET")
        response = request.urlopen(req)
        data = str(ungzip(response.read()).decode("utf-8"))
    except Exception as r:
        print(r)
        if et <= 0:
            return ''
        et -= 1
        data = getData(url,et)
    return data

def ungzip(data):
    try:
        data = gzip.decompress(data)
    except:
        pass
    return data

def replaceChr(text):
    tmp = list(repChr.keys())
    for t in tmp:
        text = text.replace(t,repChr[t])
    return text

def getMusic_tp(MusicID):
    url = 'https://api.imjad.cn/cloudmusic/?type=lyric&id='+str(MusicID)
    jsonData = json.loads(getData(url))
    try:
        lrcdata = jsonData['lrc']['lyric']
    except:
        return {}
    
    url = 'https://api.imjad.cn/cloudmusic/?type=detail&id='+str(MusicID)
    jsonData = json.loads(getData(url))['songs'][0]
    title = jsonData['name']
    cover = jsonData['al']['picUrl']
    tmp = jsonData['ar']
    singer = []
    for s in tmp:
        singer.append(s['name'])
    singer = ','.join(singer)

    return {'title':title,'singer':singer,'lrc':lrcdata,'cover':cover}
    
def getMusic_off(MusicID):
    lrcdata = json.loads(getData('http://music.163.com/api/song/media?id='+str(MusicID)))
    if "lyric" not in lrcdata:
        return {}
    
    data = getData('https://music.163.com/song?id='+str(MusicID))
    sign = r'<script type="application/ld+json">'
    i = data.find(sign) + len(sign)
    o = data.find(r'</script>',i)
    musinfo = json.loads(data[i:o])

    sign = r'<title>'
    i = data.find(sign) + len(sign)
    o = data.find('</title>',i)
    title = data[i:o]
    tmp = title.split(' - ')[-3]
    singer = tmp.replace('/',',')
    
    title = musinfo['title']
    cover = musinfo['images'][0]

    if '（原曲' in title:
        i = title.find('（原曲')
        o = title.find('）',i) + 1
        title = title.replace(title[i:o],'')

    return {'title':title,'singer':singer,'lrc':lrcdata['lyric'],'cover':cover}

class MainWindow(object):
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('CMLD GUI')
        self.window.resizable(height=False,width=False)

        self.entry_idInput = tk.Entry(self.window)
        self.label_text1 = tk.Label(self.window,text='MusicID:')
        self.button_clearInput = tk.Button(self.window,text='清空',command=self.clear)
        self.button_execute = tk.Button(self.window,text='走你',command=self.getIt)
        self.label_text2 = tk.Label(self.window,text='')
        self.label_text3 = tk.Label(self.window,text='')
        self.label_text4 = tk.Label(self.window,text='')
        self.sctext_lyricShow = scrolledtext.ScrolledText(self.window,width=40,height=13,wrap=tk.WORD)
        self.label_text5 = tk.Label(self.window,text='输出文件 :')
        self.entry_savePathShow = tk.Entry(self.window,text='',state='disabled')
        self.button_savePathSel = tk.Button(self.window,text='浏览',state='disabled',command=self.selectSavePath)
        self.button_help = tk.Button(self.window,text='帮助',command=self.showHelp)
        self.button_setting = tk.Button(self.window,text='设置',command=self.config)
        self.button_save = tk.Button(self.window,text='保存',state='disabled',command=self.save)
        self.button_exit = tk.Button(self.window,text='退出',command=exit)

        self.label_text1.grid(column=0,row=0)
        self.entry_idInput.grid(column=1,row=0)
        self.button_clearInput.grid(column=2,row=0)
        self.button_execute.grid(column=3,row=0)
        self.label_text2.grid(column=0,row=1,columnspan=4,sticky='w')
        self.label_text3.grid(column=0,row=2,columnspan=4,sticky='e')
        self.label_text4.grid(column=0,row=3,columnspan=2,sticky='w')
        self.sctext_lyricShow.grid(column=0,row=4,columnspan=4,sticky='w')
        self.label_text5.grid(column=0,row=5,sticky='w')
        self.entry_savePathShow.grid(column=1,row=5,sticky='w')
        self.button_savePathSel.grid(column=2,row=5,sticky='w')
        self.button_save.grid(column=3,row=5,sticky='w')
        self.button_setting.grid(column=3,row=6,sticky='w')
        self.button_help.grid(column=2,row=6,sticky='w')
        self.button_exit.grid(column=0,row=6,sticky='w')

        self.window.mainloop()

    def showHelp(self):
        tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message='云音乐歌词下载器 v.%s'%version)
        tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message='在输入框中输入歌曲的MusicID进行查询\n比如495645135，切记不要直接复制网址哦')
        tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message='建议将歌词文件保存为与下载的音乐文件一致的文件名，便于播放器读取呢w')
        
    def config(self):
        configWindow = ConfigWindow()
        del configWindow
    
    def clear(self):
        self.setEntry(entry=self.entry_idInput)
        self.label_text2['text'] = ''
        self.label_text3['text'] = ''
        self.setSctext(sctext=self.sctext_lyricShow)
        self.label_text4['text'] = ''
        self.setEntry(entry=self.entry_savePathShow)
        self.button_savePathSel['state'] = 'disabled'
        self.button_save['state'] = 'disabled'

    def setEntry(self,entry=None,lock=False,text=''):
        entry['state'] = 'normal'
        entry.delete(0,'end')
        entry.insert('end',text)
        if lock:
            entry['state'] = 'disabled'

    def setSctext(self,sctext=None,lock=False,add=False,text=''):
        sctext['state'] = 'normal'
        if not add:
            sctext.delete(1.0,'end')
        sctext.insert('end',text)
        if lock:
            sctext['state'] = 'disabled'

    def selectSavePath(self):
        filename = replaceChr(self.data['singer']+' - '+self.data['title']).strip()
        file = tkinter.filedialog.asksaveasfilename(title='保存为',filetypes=[('lrc歌词文件','*.lrc')],defaultextension='.lrc',initialfile=filename)
        self.setEntry(entry=self.entry_savePathShow,lock=True,text=file)

    def save(self):
        path = self.entry_savePathShow.get()
        if path == '':
            tk.messagebox.showinfo(title='(ノ▼Д▼)ノ',message='你还没选保存目录啊喂！\n是想让我刻到你DNA里吗⁄(⁄ ⁄•⁄ω⁄•⁄ ⁄)⁄')
            return
        content = self.sctext_lyricShow.get('1.0','end').strip()
        if content == '':
            tmp = tk.messagebox.askyesno(title='｡ﾟヽ(ﾟ´Д`)ﾉﾟ｡',message='歌词不见啦嘤嘤嘤(╥﹏╥)\n这是bug吧，绝对是bug吧！要不再试一次？')
            if tmp:
                self.setEntry(entry=self.entry_idInput,text=str(self.musicId))
                self.getIt()
            return
        with open(path,'w+',encoding='utf-8') as f:
            f.write(content)
        tk.messagebox.showinfo(title='ヽ(✿ﾟ▽ﾟ)ノ',message='完成！')
        

    def getIt(self):
        try:
            int(self.entry_idInput.get())
        except:
            tk.messagebox.showinfo(title='啊这？(#`Д´)ﾉ',message='你确定你输入的是MusicID？')
            return
        self.musicId = int(self.entry_idInput.get())
        if config['official_api']:
            self.data = getMusic_off(self.musicId)
        else:
            self.data = getMusic_tp(self.musicId)
        if self.data == {}:
            tk.messagebox.showinfo(title='=͟͟͞͞(꒪⌓꒪*)',message='没有找到呢。\n这可能是由于此ID对应的歌曲不存在，或者说这首歌曲没有滚动歌词。')
            return
        self.clear()
        self.label_text2['text'] = '《%s》（ID%s）'%(self.data['title'],self.musicId)
        self.label_text3['text'] = '——By: '+self.data['singer']
        self.label_text4['text'] = '歌词预览 ↓'
        self.button_savePathSel['state'] = 'normal'
        self.button_save['state'] = 'normal'
        self.setSctext(sctext=self.sctext_lyricShow,lock=True,text=self.data['lrc'])

class ConfigWindow(object):
    global config
    def __init__(self):
        self.window = tk.Tk()
        self.window.resizable(height=False,width=False)
        self.window.title('设置')

        self.frame_apiConfig = tk.LabelFrame(self.window,text='API设置')
        self.btn_offApi = tk.Button(self.frame_apiConfig,text='官方API',command=lambda x=0:self.changeAPI('official'))
        self.btn_tpApi = tk.Button(self.frame_apiConfig,text='第三方API',command=lambda x=0:self.changeAPI('third_party'))
        self.label_text1 = tk.Label(self.frame_apiConfig,text='（第三方API 由 AD\'s API 提供支持）\n注意：官方api反而可能有bug，因为是我自己研究的awa',justify='left')
        self.label_apiModeShower = tk.Label(self.frame_apiConfig,text='模式：-')
        self.btn_quit = tk.Button(self.window,text='完成',command=self.window.destroy)

        self.frame_apiConfig.grid(column=0,row=0,columnspan=2,sticky='w')
        self.btn_offApi.grid(column=0,row=0,sticky='w')
        self.btn_tpApi.grid(column=0,row=1,sticky='w')
        self.label_text1.grid(column=0,row=2,sticky='w')
        self.label_apiModeShower.grid(column=0,row=3,sticky='w')
        self.btn_quit.grid(column=1,row=1,sticky='w')

        self.update()
        self.window.mainloop()

    def changeAPI(self,apimode):
        if apimode == 'official':
            config['official_api'] = True
        elif apimode == 'third_party':
            config['official_api'] = False
        self.update()

    def update(self):
        if config['official_api']:
            self.label_apiModeShower['text'] = '当前：官方API'
        else:
            self.label_apiModeShower['text'] = '当前：第三方API'

window = MainWindow()
