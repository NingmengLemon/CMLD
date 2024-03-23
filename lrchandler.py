import re
import typing
import os
import copy

from zhconv import convert 


class LrcHandler(object):
    TIMETAG_REGEX = r"\[\s*([0-9]+)\s*\:\s*([0-9]{2})\s*[\.\:]\s*([0-9]+)\s*\]"

    EXTRATAG_REGEX = r"\[\s*([a-zA-Z]{,5})\s*\:\s*(.+?)\s*\]"

    def __init__(self, lrc_source: typing.Union[str, bytes]) -> None:
        self.raw = None
        self.file = None
        if isinstance(lrc_source, str):
            if os.path.isfile(lrc_source):
                self.file = lrc_source
                with open(lrc_source, "r", encoding="utf-8") as f:
                    self.raw = f.read()
            else:
                self.raw = lrc_source
        elif isinstance(lrc_source, bytes):
            self.raw = lrc_source.decode()
        else:
            raise AssertionError("unsupported type: %s" % type(lrc_source))

        self._content, self._extra_tags = self.extract(self.raw)

    @property
    def content(self):
        return copy.deepcopy(self._content)

    @property
    def extra_tag(self):
        return copy.deepcopy(self._extra_tags)

    @property
    def dict(self):
        return {k: v for k, v in self.content}

    def __dict__(self):
        return self.dict

    def __iter__(self):
        return iter(self.content)

    @staticmethod
    def second2time(s: float) -> str:
        return "%02d:%05.2f" % (s // 60, s % 60)

    @classmethod
    def extract(
        cls, lrc_text: str
    ) -> typing.Tuple[typing.List[typing.Tuple[int, str]], typing.Dict[str, str]]:
        extra = {
            k.strip().lower(): v.strip().lower()
            for k, v in re.findall(cls.EXTRATAG_REGEX, lrc_text)
        }
        offset = int(extra.pop("offset", "0")) / 1000

        lines = lrc_text.splitlines(keepends=False)
        result = []
        for line in lines:
            timetags = re.findall(cls.TIMETAG_REGEX, line)
            line = re.sub(cls.TIMETAG_REGEX, "", line)
            for timetag in timetags:
                m, s, cs = timetag
                timetag = round(int(m) * 60 + float(s + "." + cs), 3)
                result.append((timetag + offset, line))

        return sorted(result, key=lambda x: x[0]), extra


def combine(
    lrc_main: typing.Union[LrcHandler, str, bytes],
    lrc_sub: typing.Union[LrcHandler, str, bytes],
):
    assert isinstance(lrc_main, (LrcHandler, str, bytes)) and isinstance(
        lrc_sub, (LrcHandler, str, bytes)
    ), "invalid input data type"
    if isinstance(lrc_main, (str, bytes)):
        lrc_main = LrcHandler(lrc_main)
    if isinstance(lrc_sub, (str, bytes)):
        lrc_sub = LrcHandler(lrc_sub)
        
    d_sub = lrc_sub.dict
    result = ""
    for k, v in lrc_main.content:
        result += "\n\n[%s]%s" % (LrcHandler.second2time(k), v)
        if k in d_sub:
            result += "\n[%s]%s" % (LrcHandler.second2time(k), convert(d_sub[k],'zh-cn'))
    return result


if __name__ == "__main__":
    # multi-timetags in one line
    test_lrc = """
[00:01.83](Prelude)
[02:36.60][02:33.58][02:30.55][02:27.50][02:24.42][02:21.39][02:18.51][02:15.32][02:12.43][02:09.27][02:06.27][02:03.15][02:00.16][01:57.11][01:54.11][01:25.16][01:22.13][01:19.13][01:16.12][01:13.50][01:10.40][01:06.95][01:03.94][00:35.60][00:32.90][00:28.98][00:25.93][00:22.89][00:19.84][00:16.85][00:13.85][00:10.83][00:07.68]ファミ ファミ ファミーマ ファミファミマー
[02:16.62][01:52.54][01:02.50][00:12.25]ワン、ツー、三、四
[01:40.40][01:28.23][00:50.33][00:38.25]私の町 ふぁみふぁみま
[01:43.42][01:31.26][00:53.35][00:41.20]いつもバイト 男の子
[00:44.21]優しい目で はにかむの
[00:47.27]変に意識 どうしよう
[00:56.38]レシートごしに触れる手と
[01:49.51][00:59.39]あなたとコンピになりたいだけ
[01:34.33]元気な声 聞きたくて
[01:37.37]ランチはこ↑こ↓ って决めてるの
[01:46.48]レンジ向かう後ろ姿
[02:39.66]ファミファミファミーマッファー ミー ファー ミー マー"""
    handler = LrcHandler(test_lrc)
    for line in handler:
        print(*line)
    # combine test
    print(combine("./original.lrc", "./translated.lrc"))
