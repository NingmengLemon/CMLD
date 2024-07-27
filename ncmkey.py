import base64
import json

from Cryptodome.Cipher import AES

__all__ = ["decrypt"]

NCM_DEC_KEY = "#14ljk_!\\]&0U<'("
CRYPTOR = AES.new(NCM_DEC_KEY.encode("utf-8"), AES.MODE_ECB)


def decrypt(key: str) -> dict:
    key = key.strip().removeprefix("163 key(Don't modify):").strip()
    raw = base64.b64decode(key.encode(encoding="utf-8"))
    dec = CRYPTOR.decrypt(raw).decode(encoding="utf-8")[6:]
    meta = json.loads(dec[: dec.rfind("}") + 1])
    return meta


SAMPLE_KEY = "L64FU3W4YxX3ZFTmbZ+8/fMZ5HO+EQE0d1hry/01n1imgJAjwEU1sIK3DunPCv8JIDfFiwO6gpGCI/omCPk6o+iyDgemCERB74r1dmvVr8Wbogz195VQ2TusMWpQYrr4hv/5sNK3RLF63c1W6YvLbyvK6F1ZqljV++8nuxUKMajm+9C5eM6uLnnXsqxoZ7z6YaVNWdj+A3FGInsVRPMIxls7Lz9KplmWAGoRrSj/P2lheZZvLdikmlDL64LPYugLkxcTQfHFwdDa3NDBPsBwgNldMjhmdKGHER7CrMKF16c+IIias7TFLviRxlj1RDghodu6aXmBkJFBWP8l+2zsTlxS+EaX64C2/+fAQ7mfvO4FZvxwKtRKs+o5oQ2tsNJSvdTNTzUv8ByWjQAEvlmpzRUFACo2gQuRRis/3UGGpp78C/oUnwwIsHvW3oczICzgQBqC8V3o4OHTuKyaqOM3rb6j3NYr7FgyLwLqKc5lJlW8XfeKKdsSJkQCD4MLZqMC/hmTRvL/Ob7ebNgLIGdmL5ClgoxqZ2mphA5EFWWFZydpvvxRrsv8frGMDb/Hd/EdB11TFPcrhCcM9Vd5l+xznQ=="

if __name__ == "__main__":
    info = decrypt(SAMPLE_KEY)
    print(json.dumps(info, ensure_ascii=False, indent=4))
