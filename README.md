# CMLD

CloudMusic Lyric Downloader

云音乐歌词下载器

项目，复活了……！

## 功能简介

功能 | 备注
------- | ---
通过MusicID或Url下载歌词 | 
通过AlbumID或Url解析专辑并下载歌词 |
扫描文件夹并为音频文件匹配下载合适的歌词 | 模糊匹配
手动指定音频文件并为其匹配下载合适的歌词 | 模糊匹配

注意：匹配文件时按 163Key -> Tag -> 文件名 的优先级进行匹配

注意：歌词文件命名：artist1,artist2,...,artistn - title.lrc

注意：歌词文件编码：UTF-8

注意：网络错误最多重试 3 次

## 关于 163 Key：

参考：

[163 key 使用指南](https://www.morfans.cn/archives/2793)

[python_AES-ECB加密、解密方法](https://blog.csdn.net/qq_45664055/article/details/123348485)

## 关于 Music Tag：

引用项目：[TinyTag](https://github.com/devsnd/tinytag)

## 关于制作动机：

咱喜欢用的播放器是 Foobar2000，但咱感觉它的歌词匹配机制做得不到位，同时咱也需要在MP3上听歌，因此就想到了自己写一个lrc歌词下载器 (。・∀・)ノ

然后咱发现网易云的歌词api和搜索api居然没有加密，而且网页的专辑页面的源代码里可以找到预请求的专辑信息，而咱又正好会点Python，于是就开始动手了 o((>ω< ))o

（其实一开始用的是[AD's API](api.imjad.cn)和[Hitokoto API](https://github.com/a632079/teng-koa/blob/master/netease.md)来着，后来发现访问困难，于是就自己去找了两个官方的w
