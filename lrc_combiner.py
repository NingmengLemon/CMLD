import os
import re
import logging


class EnhancedFormatIsNotSupported(Exception):
    def __init__(self, file):
        self.file = file
        self._msg = file

    def __str__(self):
        return self._msg


regex_enhanced_tag = r"\<[0-9]+\:[0-9]{2}\.[0-9]+\>"
regex_lrcline = r"\[([0-9]+)\:([0-9]{2}\.[0-9]+)\](.*)"


def second2time(s: float) -> str:
    s_ = s % 60
    m = (s - s_) / 60
    return "%02d:%05.2f" % (m, s_)


def combine_legacy(file_1: str, file_2: str, savefile: str) -> None:
    with open(file_1, "r", encoding="utf-8") as f:
        file_1 = f.read()
    with open(file_2, "r", encoding="utf-8") as f:
        file_2 = f.read()
    lrcs = []
    for h, m, l in re.findall(regex_lrcline, file_1):
        h = int(h)
        m = float(m) + h * 60
        lrcs += [(m, l)]
    for h, m, l in re.findall(regex_lrcline, file_2):
        h = int(h)
        m = float(m) + h * 60
        lrcs += [(m, l + "\n")]
    lrcs = sorted(lrcs, key=lambda x: x[0])
    for i in range(len(lrcs)):
        m = lrcs[i][0] % 60
        h = (lrcs[i][0] - m) / 60
        l = lrcs[i][1]
        lrcs[i] = "[%02d:%05.2f]%s\n" % (h, m, l)
    with open(savefile, "w+", encoding="utf-8") as f:
        f.writelines(lrcs)


class LrcHandler(object):
    def __init__(self, data: str):
        self.data = data
        self.lrclines = [
            (float(s) + int(m) * 60, l) for m, s, l in re.findall(regex_lrcline, data)
        ]
        self.timedict = {k: v for k, v in self.lrclines}

    def get_all_timestamps(self) -> list:
        return list(self.timedict.keys())

    def generator_text(self):
        for t, l in self.lrclines:
            yield "[" + second2time(t) + "]" + l

    def generator(self):
        for t, l in self.lrclines:
            yield t, l

    def get(self, r: range) -> list:
        res = []
        for i in range(len(self.lrclines)):
            if self.lrclines[i][0] in r:
                res += [self.lrclines[i]]
        return res


def combine(file_main: str, file_sub: str, outfp: str) -> None:
    res = ""
    with open(file_main, "r", encoding="utf-8") as f:
        lrc_main = f.read()
    lrc_main = LrcHandler(lrc_main)
    with open(file_sub, "r", encoding="utf-8") as f:
        lrc_sub = f.read()
    lrc_sub = LrcHandler(lrc_sub)
    all_ts = sorted(set(lrc_main.get_all_timestamps() + lrc_sub.get_all_timestamps()))
    for ts in all_ts:
        if ts in lrc_main.timedict:
            res += "[%s]%s\n" % (second2time(ts), lrc_main.timedict[ts])
        if ts in lrc_sub.timedict:
            res += "[%s]%s\n" % (second2time(ts), lrc_sub.timedict[ts])
        res += "\n"
    with open(outfp, "w+", encoding="utf-8") as f:
        f.write(res)
    logging.info(
        'Merged lrc files: "{}" & "{}" >> "{}"'.format(file_main, file_sub, outfp)
    )
