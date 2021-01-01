import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
from tkinter import ttk,scrolledtext
from urllib import request,parse
import json,gzip,os,sys,time

version = '1.3.1.20210101_beta'
config = {'yiyan':True,
          'outfile_format':'{singer} - {song}',
          'singer_sepchar':','}

workDir = os.getcwd()
    
#code解释:
#0     内部错误
#-1    没有数据
#其他  http状态码

def updateConfigFile(path=workDir+'\\CMLD_config.json',mode='load'):#mode = release / load
    global config
    if mode == 'load':
        if os.path.exists(path):
            config = json.load(open(path,'r'))
        else:
            json.dump(config,open(path,'w+',encoding='utf-8'))
    elif mode == 'release':
        json.dump(config,open(path,'w+',encoding='utf-8'))

def getData(url,timeout=5,headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1"},dict={}):
    if url[:8] != "https://" and url[:7] != "http://":
        url = "https://" + url
    data = bytes(parse.urlencode(dict),encoding="utf-8")
    req = request.Request(url=url,data=data,headers=headers,method="GET")
    try:
        response = request.urlopen(req,timeout=timeout)
        data = response.read()
        code = response.getcode()
    except Exception as e:
        try:
            code = response.getcode()
        except:
            code = 0
        return {'data':None,'code':0,'error':str(e)}
    try:
        data = gzip.decompress(data)
        gz = True
    except:
        gz = False
    data = str(data.decode("utf-8"))
    return {'data':data,'gzip':gz,'code':code}

def replaceChr(text):#处理非法字符
    repChr = {'/':'／',
              '*':'＊',
              ':':'：',
              '\\':'＼',
              '>':'＞',
              '<':'＜',
              '|':'｜',
              '?':'？'}
    tmp = list(repChr.keys())
    for t in tmp:
        text = text.replace(t,repChr[t])
    return text

def getMusic(MusicID):
    tmp = getData('http://music.163.com/api/song/media?id='+str(MusicID))
    if tmp['data'] == None:
        return {'error':tmp['error'],'code':tmp['code']}
    lrcdata = json.loads(tmp['data'])
    if "lyric" not in lrcdata:
        return {'error':'No Lyrics.','code':-1}
    lrcdata = lrcdata['lyric'].strip()

    url = 'https://api.imjad.cn/cloudmusic/?type=detail&id='+str(MusicID)
    data = getData(url)
    if data['data'] == None:
        return {'error':data['error'],'code':data['code']}
    jsonData = json.loads(data['data'])['songs'][0]
    title = jsonData['name']
    cover = jsonData['al']['picUrl']
    tmp = jsonData['ar']
    singer = []
    for s in tmp:
        singer.append(s['name'])
    singer = config['singer_sepchar'].join(singer)

    return {'title':title,'singer':singer,'lrc':lrcdata,'cover':cover}

def getMusic_thirdparty_spare(MusicID):#备用
    url = 'https://api.imjad.cn/cloudmusic/?type=lyric&id='+str(MusicID)
    tmp = getData(url)
    if tmp['data'] == None:
        return {'error':tmp['error'],'code':tmp['code']}
    jsonData = json.loads(tmp['data'])
    try:
        lrcdata = jsonData['lrc']['lyric']
    except:
        return {'error':'No Lyrics.','code':-1}
    
    url = 'https://api.imjad.cn/cloudmusic/?type=detail&id='+str(MusicID)
    data = getData(url)
    if data['data'] == None:
        return {'error':tmp['error'],'code':tmp['code']}
    jsonData = json.loads(data['data'])['songs'][0]
    title = jsonData['name']
    cover = jsonData['al']['picUrl']
    tmp = jsonData['ar']
    singer = []
    for s in tmp:
        singer.append(s['name'])
    singer = config['singer_sepchar'].join(singer)

    return {'title':title,'singer':singer,'lrc':lrcdata,'cover':cover}
    
def getMusic_official_spare(MusicID):#备用
    tmp = getData('http://music.163.com/api/song/media?id='+str(MusicID))
    if tmp['data'] == None:
        return {'error':tmp['error'],'code':tmp['code']}
    lrcdata = json.loads(tmp['data'])
    if "lyric" not in lrcdata:
        return {'error':'No Lyrics.','code':-1}
    lrcdata = lrcdata['lyric']
    
    data = getData('https://music.163.com/song?id='+str(MusicID))['data']
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

def searchMusic(keyword):
    url = 'https://v1.hitokoto.cn/nm/search/'+parse.quote(keyword)
    tmp = getData(url)
    if tmp['data'] == None:
        return {'error':tmp['error'],'code':tmp['code']}
    try:
        tmpdata = json.loads(tmp['data'])['result']['songs']
    except:
        return {'error':'No Search Result.','code':-1}
    retData = {}
    for obj in tmpdata:
        ar = []
        for i in obj['artists']:
            ar.append(i['name'])
        ar = ','.join(ar)
        retData[obj['id']] = {'id':obj['id'],'name':obj['name'],'artists':ar,'album':obj['album']['name']}
    return retData

def getAlbum(albumId):
    url = 'https://api.imjad.cn/cloudmusic/?type=album&id='+str(albumId)
    tmp = getData(url)
    if tmp['data'] == None:
        return {'error':tmp['error'],'code':tmp['code']}
    try:
        tmpdata = json.loads(tmp['data'])['songs']
    except:
        return {'error':'No Album.','code':-1}
    retData = {}
    for obj in tmpdata:
        ar = []
        for i in obj['ar']:
            ar.append(i['name'])
        ar = ','.join(ar)
        retData[obj['id']] = {'id':obj['id'],'name':obj['name'],'artists':ar,'album':obj['al']['name']}
    return retData

class MainWindow(object):
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('CMLD主窗口')
        self.window.resizable(height=False,width=False)
        self.window.protocol('WM_DELETE_WINDOW',self.close)

        self.entry_idInput = tk.Entry(self.window)
        self.label_text1 = tk.Label(self.window,text='MusicID: ')
        self.entry_idInput.bind("<Return>",self.getIt_clone)
        self.button_clearInput = tk.Button(self.window,text='清空',command=self.clear)
        self.button_execute = tk.Button(self.window,text='走你',command=self.getIt)
        self.label_text2 = tk.Label(self.window,text='')
        self.label_text3 = tk.Label(self.window,text='')
        self.label_text4 = tk.Label(self.window,text='')
        self.sctext_lyricShow = scrolledtext.ScrolledText(self.window,width=40,height=13,wrap=tk.WORD,state='disabled',selectbackground='#66CCFF')
        self.label_text5 = tk.Label(self.window,text='输出文件 :')
        self.entry_savePathShow = tk.Entry(self.window,text='',state='disabled')
        self.button_savePathSel = tk.Button(self.window,text='浏览',state='disabled',command=self.selectSavePath)
        self.button_help = tk.Button(self.window,text='帮助',command=self.showHelp)
        self.button_setting = tk.Button(self.window,text='设置',command=self.config)
        self.button_save = tk.Button(self.window,text='保存',state='disabled',command=self.save)
        self.button_exit = tk.Button(self.window,text='退出',command=self.close)
        self.frame_extraFunc = tk.LabelFrame(self.window,text='拓展功能')
        self.button_search = tk.Button(self.frame_extraFunc,text='搜索歌曲',command=self.search)
        self.button_getAlbum = tk.Button(self.frame_extraFunc,text='解析专辑',command=self.album)
        self.label_yiyan = tk.Label(self.window,text='')
        self.label_yiyan.bind('<Button-1>',self.updateYiyan)
        

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
        self.frame_extraFunc.grid(column=0,row=7,columnspan=4,sticky='w',ipadx=100)
        self.button_search.grid(column=0,row=0,sticky='w')
        self.button_getAlbum.grid(column=1,row=0,sticky='w')
        self.label_yiyan.grid(column=0,row=8,sticky='w',columnspan=4)

        if config['yiyan']:
            self.updateYiyan()
        self.window.mainloop()

    def close(self):
        self.window.quit()
        self.window.destroy()

    def showHelp(self):
        text = ['云音乐歌词下载器 v.%s'%version,
                '在输入框中输入歌曲的MusicID进行查询\n比如495645135，切记不要直接复制网址哦',
                '建议将歌词文件保存为与下载的音乐文件一致的文件名，\n以便于播放器读取呢',
                '歌词文件的文件名的格式是可以在设置中进行改动的哦',
                '更多功能详见"拓展功能"区域.',
                '如果想要下载无版权音乐，可以走代理↓\nhttps://wy.ydlrqx.com/proxy.pac']
        for t in text:
            tk.messagebox.showinfo(title='(⑅˃◡˂⑅)',message=t)
        
    def config(self):
        self.button_setting['state'] = 'disabled'
        configWindow = ConfigWindow()
        self.button_setting['state'] = 'normal'
    
    def clear(self):
        self.setEntry(entry=self.entry_idInput)
        self.label_text2['text'] = ''
        self.label_text3['text'] = ''
        self.setSctext(sctext=self.sctext_lyricShow,lock=True)
        self.label_text4['text'] = ''
        self.setEntry(entry=self.entry_savePathShow,lock=True)
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
        filename = self.makeFilename(self.data['singer'],self.data['title'])
        file = tkinter.filedialog.asksaveasfilename(title='保存为',filetypes=[('lrc歌词文件','*.lrc')],defaultextension='.lrc',initialfile=filename)
        self.setEntry(entry=self.entry_savePathShow,lock=True,text=file)

    def save(self,path=None,ignoreError=False):
        if path == None:
            path = self.entry_savePathShow.get()
        if path == '':
            if not ignoreError: 
                tk.messagebox.showinfo(title='(ノ▼Д▼)ノ',message='你还没选保存目录啊喂！\n是想让我刻到你DNA里吗⁄(⁄ ⁄•⁄ω⁄•⁄ ⁄)⁄')
            return
        content = self.sctext_lyricShow.get('1.0','end').strip()
        if content == '':
            if not ignoreError:
                tmp = tk.messagebox.askyesno(title='｡ﾟヽ(ﾟ´Д`)ﾉﾟ｡',message='歌词不见啦嘤嘤嘤(╥﹏╥)\n这是bug吧，绝对是bug吧！要不再试一次？')
                if tmp:
                    self.setEntry(entry=self.entry_idInput,text=str(self.musicId))
                    self.getIt()
            return
        with open(path,'w+',encoding='utf-8') as f:
            f.write(content)
        if not ignoreError:
            tk.messagebox.showinfo(title='ヽ(✿ﾟ▽ﾟ)ノ',message='完成！')

    def getIt_clone(self,self_):#供bind调用的克隆函数
        self.getIt()

    def makeFilename(self,singer,title):
        tmp = config['outfile_format'].replace('{singer}',singer)
        tmp = tmp.replace('{song}',title)
        filename = replaceChr(tmp).strip()
        return filename

    def getIt(self,MusicID=None,ignoreError=False,autoSave=False):
        if MusicID == None:
            MusicID = self.entry_idInput.get()
        try:
            int(MusicID)
        except:
            if not ignoreError:
                tk.messagebox.showwarning(title='∑(✘Д✘๑ ) ',message='你确定你输入的是MusicID？')
            return
        self.musicId = int(MusicID)
        self.data = getMusic(self.musicId)
        if 'error' in self.data:
            if not ignoreError:
                if self.data['code'] == -1:
                    tk.messagebox.showinfo(title='=͟͟͞͞(꒪⌓꒪*)',message='没有找到呢。\n这可能是由于此ID对应的歌曲不存在，或者说这首歌曲没有滚动歌词。')
                else:
                    tk.messagebox.showerror(title='=͟͟͞͞(꒪⌓꒪*)',message='Error:%s\n%s'%(self.data['code'],self.data['error']))
            return
        self.clear()
        self.label_text2['text'] = '《%s》（ID%s）'%(self.data['title'],self.musicId)
        self.label_text3['text'] = '——By: '+self.data['singer']
        self.label_text4['text'] = '歌词预览 ↓'
        self.button_savePathSel['state'] = 'normal'
        self.button_save['state'] = 'normal'
        self.setSctext(sctext=self.sctext_lyricShow,lock=True,text=self.data['lrc'])
        if autoSave:
            if not os.path.exists('./CMLD_AutoSave/'):
                os.mkdir('./CMLD_AutoSave/')
            filename = self.makeFilename(self.data['singer'],self.data['title'])+'.lrc'
            path = './CMLD_AutoSave/'+filename
            self.save(path,ignoreError=True)

    def updateYiyan(self,self_=None):
        tmp = getData('v1.hitokoto.cn')
        if 'error' in tmp:
            tk.messagebox.showwarning(title='=͟͟͞͞(꒪⌓꒪*)',message='一言加载失败。')
            return
        self.label_yiyan['text'] = json.loads(tmp['data'])["hitokoto"]

    def search(self):
        self.button_search['state'] = 'disabled'
        searchWindow = SearchWindow()
        self.batch(searchWindow.returnList)
        self.button_search['state'] = 'normal'

    def album(self):
        self.button_getAlbum['state'] = 'disabled'
        albumWindow = AlbumWindow()
        self.batch(albumWindow.returnList)
        self.button_getAlbum['state'] = 'normal'

    def batch(self,idList):
        if len(idList) == 1:
            self.getIt(idList[0])
            return
        elif len(idList) < 1:
            return
        print('批处理正在运行')
        self.clear()
        self.button_execute['state'] = 'disabled'
        for i in idList:
            self.getIt(i,ignoreError=True,autoSave=True)
            print('批处理 进度%s/%s'%(idList.index(i)+1,len(idList)))
        self.button_execute['state'] = 'normal'
        self.clear()
        if tk.messagebox.askyesno(title='ヽ(✿ﾟ▽ﾟ)ノ',message='完成：%s 个MusicID的获取\n如果没有你要的文件，则有可能发生了错误，或者这首歌没有歌词.\n要打开输出目录吗？'%len(idList)):
            os.system('explorer "%s"'%(os.path.abspath('./CMLD_AutoSave/')))
        print('批处理已完成')
        

class ConfigWindow(object):
    global config
    def __init__(self):
        self.window = tk.Tk()
        self.window.resizable(height=False,width=False)
        self.window.title('设置')
        #关于
        self.frame_about = tk.LabelFrame(self.window,text='关于')
        self.label_about1 = tk.Label(self.frame_about,text='使用API：\n  云音乐官方API\n  AD\'s API\n  Hitokoto API',justify='left')
        #输出文件名格式
        self.frame_outFormat = tk.LabelFrame(self.window,text='输出文件名')
        self.label_outFmShow = tk.Label(self.frame_outFormat,text='-')
        self.button_fmSwitch = tk.Button(self.frame_outFormat,text='切换',command=self.changeFilename)
        #一言
        self.frame_yiyan = tk.LabelFrame(self.window,text='一言')
        self.label_yyShow = tk.Label(self.frame_yiyan,text='-')
        self.button_yySwitch = tk.Button(self.frame_yiyan,text='切换',command=self.changeYiyan)
        #歌手分割字符
        self.frame_singerSepchar = tk.LabelFrame(self.window,text='歌手分割字符')
        self.label_sscText = tk.Label(self.frame_singerSepchar,text='当前：')
        self.label_sscShow = tk.Label(self.frame_singerSepchar,text='-',bg='#acfff1',width=5)
        self.entry_sscInput = tk.Entry(self.frame_singerSepchar,width=5)
        self.button_sscUse = tk.Button(self.frame_singerSepchar,text='应用',command=self.changeSepchar)
        #完成按钮
        self.btn_quit = tk.Button(self.window,text='完成',command=self.close)
        #布局
        self.frame_about.grid(column=0,row=0,columnspan=3)
        self.label_about1.grid(column=0,row=0)
        self.frame_yiyan.grid(column=0,row=1)
        self.label_yyShow.grid(column=0,row=0)
        self.button_yySwitch.grid(column=1,row=0)
        self.frame_outFormat.grid(column=1,row=1)
        self.label_outFmShow.grid(column=0,row=0)
        self.button_fmSwitch.grid(column=0,row=1)
        self.frame_singerSepchar.grid(column=2,row=1)
        self.label_sscText.grid(column=0,row=0)
        self.label_sscShow.grid(column=1,row=0)
        self.entry_sscInput.grid(column=0,row=1)
        self.button_sscUse.grid(column=1,row=1)

        self.btn_quit.grid(column=0,row=2,sticky='w')

        self.InsideOutFormat = ['{singer} - {song}','{song} - {singer}','{song}']
        self.outFormatIndex = 0

        self.update()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.mainloop()

    def changeYiyan(self):
        if config['yiyan']:
            config['yiyan'] = False
        else:
            config['yiyan'] = True
        self.update()

    def changeFilename(self):
        self.outFormatIndex = (self.outFormatIndex+1)%(len(self.InsideOutFormat))
        config['outfile_format'] = self.InsideOutFormat[self.outFormatIndex]
        self.update()

    def changeSepchar(self):
        spc = self.entry_sscInput.get()
        if spc == '':
            return
        config['singer_sepchar'] = spc
        self.setEntry(entry=self.entry_sscInput)
        self.update()

    def update(self):
        if config['yiyan']:
            self.label_yyShow['text'] = '开'
        else:
            self.label_yyShow['text'] = '关'
        self.label_outFmShow['text'] = config['outfile_format']
        self.label_sscShow['text'] = config['singer_sepchar']

    def setEntry(self,entry=None,lock=False,text=''):
        entry['state'] = 'normal'
        entry.delete(0,'end')
        entry.insert('end',text)
        if lock:
            entry['state'] = 'disabled'
            
    def close(self):
        updateConfigFile(mode='release')
        self.window.quit()
        self.window.destroy()

class SearchWindow(object):
    def __init__(self):
        self.window = tk.Tk()
        self.window.resizable(height=False,width=False)
        self.window.title('搜索')
        self.window.protocol('WM_DELETE_WINDOW',self.close)

        self.label_text1 = tk.Label(self.window,text='关键词：')
        self.entry_kwinput = tk.Entry(self.window)
        self.entry_kwinput.bind('<Return>',self.search_clone)
        self.button_search = tk.Button(self.window,text='搜索',command=self.search)
        self.button_addtoline = tk.Button(self.window,text='添加选中项到准备区域\n----->',command=self.addToPrep)
        self.frame_preview = tk.LabelFrame(self.window,text='准备区域')
        self.libo_prev = tk.Listbox(self.frame_preview,selectmode='extended',selectbackground='#66CCFF')
        self.button_remSelPre = tk.Button(self.frame_preview,text='移除选中项',command=self.removeSel)
        self.button_remAll = tk.Button(self.frame_preview,text='移除所有',command=lambda x=0:self.libo_prev.delete(0,'end'))
        self.button_close = tk.Button(self.window,text='关闭',command=self.close)
        self.button_connect = tk.Button(self.frame_preview,text='开始',command=self.connect)

        self.bar_tbscbar = tk.Scrollbar(self.window,orient='vertical')
        self.table = ttk.Treeview(self.window,show="headings",columns=("id","name","singer","album"),yscrollcommand=self.bar_tbscbar.set,height=20)
        self.bar_tbscbar['command'] = self.table.yview
        self.table.column("id", width=100)
        self.table.column("name", width=100)
        self.table.column("singer", width=100)
        self.table.column("album", width=100)
        self.table.heading("id", text="MusicID")
        self.table.heading("name", text="曲名")
        self.table.heading("singer", text="歌手")
        self.table.heading("album", text="专辑")

        self.label_text1.grid(column=0,row=0,sticky='e')
        self.entry_kwinput.grid(column=1,row=0,sticky='w')
        self.button_search.grid(column=2,row=0,sticky='w')
        self.table.grid(column=0,row=1,columnspan=3)
        self.bar_tbscbar.grid(column=3,row=1,sticky='nw',ipady=190)
        self.button_addtoline.grid(column=2,row=2)
        self.button_close.grid(column=0,row=2)
        self.frame_preview.grid(column=4,row=1,ipady=100)
        self.libo_prev.grid(column=0,row=0,columnspan=2)
        self.button_remSelPre.grid(column=0,row=1)
        self.button_remAll.grid(column=1,row=1)
        self.button_connect.grid(column=0,row=2,columnspan=2)

        self.returnList = []

        self.window.mainloop()

    def close(self):
        self.window.quit()
        self.window.destroy()

    def removeSel(self):
        selection = self.libo_prev.curselection()
        for index in selection:
            self.libo_prev.delete(index)

    def setEntry(self,entry=None,lock=False,text=''):
        entry['state'] = 'normal'
        entry.delete(0,'end')
        entry.insert('end',text)
        if lock:
            entry['state'] = 'disabled'

    def addToPrep(self):
        if self.table.selection() == ():
            return
        sel = []
        for item in self.table.selection():
            sel.append(self.table.item(item,"values"))
        for item in sel:
            if item[0] not in self.libo_prev.get(0,'end'):
                self.libo_prev.insert('end',item[0])
        
    def search(self):
        keyword = self.entry_kwinput.get().strip()
        if keyword == '':
            return
        sear_res = searchMusic(keyword)
        if 'error' in sear_res:
            if sear_res['code'] == -1:
                tk.messagebox.showinfo(title='=͟͟͞͞(꒪⌓꒪*)',message='没有搜索结果。')
            else:
                tk.messagebox.showerror(title='=͟͟͞͞(꒪⌓꒪*)',message='Error:%s\n%s'%(sear_res['code'],sear_res['error']))
            return
        ids = list(sear_res.keys())
        for i in self.table.get_children():
            self.table.delete(i)
        for i in ids:
            self.table.insert("","end",values=(str(i),sear_res[i]['name'],sear_res[i]['artists'],sear_res[i]['album']))
            
        self.setEntry(entry=self.entry_kwinput)

    def search_clone(self,self_):#供bind调用的克隆函数
        self.search()

    def connect(self):
        content = self.libo_prev.get(0,'end')
        if content == ():
            return
        self.returnList += content
        self.close()

class AlbumWindow(object):
    def __init__(self):
        self.window = tk.Tk()
        self.window.resizable(height=False,width=False)
        self.window.title('专辑解析')
        self.window.protocol('WM_DELETE_WINDOW',self.close)

        self.label_text1 = tk.Label(self.window,text='专辑ID: ')
        self.entry_idInput = tk.Entry(self.window)
        self.entry_idInput.bind('<Return>',self.getList_clone)
        self.button_start = tk.Button(self.window,text='走你',command=self.getList)
        self.label_text2 = tk.Label(self.window,text='')

        self.bar_tbscbar = tk.Scrollbar(self.window,orient='vertical')
        self.table = ttk.Treeview(self.window,show="headings",columns=("id","name","singer"),yscrollcommand=self.bar_tbscbar.set,height=20)
        self.bar_tbscbar['command'] = self.table.yview
        self.table.column("id", width=100)
        self.table.column("name", width=200)
        self.table.column("singer", width=150)
        self.table.heading("id", text="MusicID")
        self.table.heading("name", text="曲名")
        self.table.heading("singer", text="歌手")

        self.button_quit = tk.Button(self.window,text='关闭',command=self.close)
        self.button_getAll = tk.Button(self.window,text='获取全部',command=self.connect_all)
        self.button_getSel = tk.Button(self.window,text='获取选中',command=self.connect_selected)

        self.label_text1.grid(column=0,row=0,sticky='e')
        self.entry_idInput.grid(column=1,row=0,sticky='w')
        self.button_start.grid(column=2,row=0,sticky='w')
        self.label_text2.grid(column=0,row=1,sticky='w',columnspan=3)
        self.table.grid(column=0,row=2,columnspan=3)
        self.bar_tbscbar.grid(column=3,row=2,sticky='w',ipady=190)
        self.button_quit.grid(column=0,row=3,sticky='w')
        self.button_getAll.grid(column=1,row=3,sticky='e')
        self.button_getSel.grid(column=2,row=3,sticky='e')

        self.returnList = []

        self.window.mainloop()

    def close(self):
        self.window.quit()
        self.window.destroy()

    def setEntry(self,entry=None,lock=False,text=''):
        entry['state'] = 'normal'
        entry.delete(0,'end')
        entry.insert('end',text)
        if lock:
            entry['state'] = 'disabled'

    def getList(self,albumId=None):
        if albumId == None:
            albumId = self.entry_idInput.get().strip()
        try:
            albumId = int(albumId)
        except:
            tk.messagebox.showwarning(title='∑(✘Д✘๑ ) ',message='你输入的是个什么东西嘛，重来！')
            return
        data = getAlbum(albumId)
        if 'error' in data:
            if data['code'] == -1:
                tk.messagebox.showinfo(title='=͟͟͞͞(꒪⌓꒪*)',message='专辑不存在.')
            else:
                tk.messagebox.showerror(title='=͟͟͞͞(꒪⌓꒪*)',message='Error:%s\n%s'%(data['code'],data['error']))
            return
        ids = list(data.keys())
        for i in self.table.get_children():
            self.table.delete(i)
        for i in ids:
            self.table.insert("","end",values=(str(i),data[i]['name'],data[i]['artists']))
        self.label_text2['text'] = '《%s》'%data[ids[0]]['album']
        self.setEntry(entry=self.entry_idInput)
        
    def getList_clone(self,self_):
        self.getList()

    def connect_selected(self):
        if self.table.selection() == ():
            return
        sel = []
        for item in self.table.selection():
            sel.append(self.table.item(item,"values")[0])
        self.returnList = sel
        self.close()

    def connect_all(self):
        tmp = []
        for i in self.table.get_children():
            tmp.append(self.table.item(i,'values')[0])
        if tmp == []:
            return
        self.returnList = tmp
        self.close()
        

if __name__ == "__main__":
    print('如果你看到了这行字，说明我还在运行_(:3 ⌒ﾞ)_')
    updateConfigFile(mode='load')
    window = MainWindow()
    sys.exit(0)
