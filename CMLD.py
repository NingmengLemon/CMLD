import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
from tkinter import scrolledtext
from urllib import request,parse
import json,gzip,os,re
from sys import exit

version = '1.0.0.20201206_beta'
api = r'http://music.163.com/api/song/media?id={id}'
mainurl = r'https://music.163.com/song?id={id}'

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

def getInfo(data):
    sign = r'<script type="application/ld+json">'
    i = data.find(sign) + len(sign)
    o = data.find(r'</script>',i)
    return json.loads(data[i:o])

def getSinger(data):
    sign = r'<title>'
    i = data.find(sign) + len(sign)
    o = data.find('</title>',i)
    title = data[i:o]
    tmp = title.split(' - ')
    singer = tmp[-3]
    return singer.replace('/',',')

def removeDk(s):
    if '（原曲' not in s:
        return s
    i = s.find('（原曲')
    o = s.find('）',i) + 1
    s = s.replace(s[i:o],'')
    return s
    
def getLyrics(MusicID):
    lrcdata = json.loads(getData(api.replace(r'{id}',str(MusicID))))
    if "lyric" not in lrcdata:
        return {}
    data = getData(mainurl.replace(r'{id}',str(MusicID)))
    musinfo = getInfo(data)
    singer = getSinger(data)
    title = musinfo['title']
    return {'title':removeDk(title),'singer':singer,'info':musinfo,'lrc':lrcdata['lyric']}

class GUI(object):
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
        self.button_help.grid(column=2,row=6,columnspan=2)
        self.button_exit.grid(column=0,row=6)

        self.window.mainloop()

    def showHelp(self):
        tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message='网易云歌词下载器 v.%s'%version)
        tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message='在输入框中输入歌曲的MusicID进行查询\n比如495645135，切记不要直接复制网址哦')
        tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message='建议将歌词文件保存为与下载的音乐文件一致的文件名，便于播放器读取呢w')
        

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
        filename = self.data['singer']+' - '+self.data['title']
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
        self.data = getLyrics(self.musicId)
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
        
window = GUI()
