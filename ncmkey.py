import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json

__all__ = ["parse"]


# https://blog.csdn.net/qq_45664055/article/details/123348485
class EncryptDate:
    def __init__(self, key):
        # 初始化密钥
        self.key = key
        # 初始化数据块大小
        self.length = AES.block_size
        # 初始化AES,ECB模式的实例
        self.aes = AES.new(self.key.encode("utf-8"), AES.MODE_ECB)
        # 截断函数，去除填充的字符
        self.unpad = lambda date: date[0 : -ord(date[-1])]

    def fill_method(self, aes_str):
        """pkcs7补全"""
        pad_pkcs7 = pad(aes_str.encode("utf-8"), AES.block_size, style="pkcs7")

        return pad_pkcs7

    def encrypt(self, encrData):
        # 加密函数,使用pkcs7补全
        res = self.aes.encrypt(self.fill_method(encrData))
        # 转换为base64
        msg = str(base64.b64encode(res), encoding="utf-8")

        return msg

    def decrypt(self, decrData):
        # base64解码
        res = base64.decodebytes(decrData.encode("utf-8"))
        # 解密函数
        msg = self.aes.decrypt(res).decode("utf-8")

        return self.unpad(msg)


_e = EncryptDate(key="#14ljk_!\]&0U<'(")


def parse(key: str) -> dict:
    return json.loads(_e.decrypt(key)[6:])
