## CMLD

(Simple) (Netease) CloudMusic Lyrics Downloader

wyy音乐歌词下载器

项目，复活了……！

### 功能列表

功能 | 备注
------- | ---
通过 MusicID 或 URL 下载歌词 | 
通过 AlbumID 或 URL 下载整个专辑的歌词 |
扫描文件夹并为音频文件匹配下载歌词 | 不含 163key 的话就模糊匹配 
手动指定音频文件并为其匹配下载歌词 | 不含 163key 的话就模糊匹配 
能够将原始歌词与翻译歌词合并成带参照行的歌词 |  
算是勉强支持了命令行调用（） |  

注意：匹配文件时按 163Key -> Tag -> 文件名 的优先级进行匹配

注意：输出的歌词文件命名：artist1,artist2,...,artistN - title.lrc

注意：歌词文件编码：UTF-8

注意：网络错误最多重试 3 次

### 感谢：

[TinyTag](https://github.com/devsnd/tinytag)，一个小巧的标签读取库。
