__all__ = (
    'AttrGettingProxy',
    'CaseInsensitiveDict',
    'DictSerializer',
    'MockName',
)

from collections import UserDict
from itertools import chain
from typing import Any


class AttrGettingProxy:
    """使被包裹的对象 `obj` 只向外暴露获取属性的功能.

    这个类也可以稍作改动用于其他用处, 例如可以只实现 `__iter__`.
    """

    def __init__(self, obj: Any):
        self._obj = obj

    def __getattr__(self, item):
        return getattr(self._obj, item)


class CaseInsensitiveDict(UserDict):
    """无视大小写的字典. (可作为其他自定义字典的参考)

    主要 override 下面四个方法, 其他方法会依赖这些.
      - `__getitem__`
      - `__setitem__`
      - `__delitem__`
      - `__contains__`
    """

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __delitem__(self, key):
        super().__delitem__(key.lower())

    def __contains__(self, key):
        return isinstance(key, str) and super().__contains__(key.lower())


class DictSerializer:
    """字典序列化. (可作为其他字符串处理的参考)

    字典有以下规则:
      - key 必须是字符串.
      - value 只能是字符串或列表, 列表中的每一项必须是字符串.

    序列化规则:
      - 使用 ':' 分割 `item` 中的键值, 使用 '|' 分割每个 `item`
      - 使用 '$' 作为转义字符串. ':' -> '$,', '|' -> '$;', '$' -> '$$'
    """

    @classmethod
    def encode(cls, data: dict) -> str:
        if not data:
            return ''
        segs = []
        for k, v in data.items():
            if isinstance(v, str):
                k = cls._encode_s(k)
                v = cls._encode_s(v)
                segs.append(':'.join((k, v)))
            elif isinstance(v, list):
                segs.append(':'.join(cls._encode_s(item) for item in chain([k], v)))
        return '|'.join(segs)

    @classmethod
    def decode(cls, s: str) -> dict:
        if not s:
            return {}
        data = {}
        segs = s.split('|')
        for seg in segs:
            kv = seg.split(':')
            if len(kv) < 2:
                continue
            if len(kv) == 2:
                k, v = kv
                k = cls._decode_s(k)
                v = cls._decode_s(v)
                data[k] = v
            else:
                k, *v = kv
                k = cls._decode_s(k)
                v = [cls._decode_s(item) for item in v]
                data[k] = v
        return data

    @staticmethod
    def _encode_s(s: str) -> str:
        return s.replace('$', '$$').replace(':', '$,').replace('|', '$;')

    @staticmethod
    def _decode_s(s: str) -> str:
        return s.replace('$;', '|').replace('$,', ':').replace('$$', '$')


class MockName:
    """mock 某个特定的属性. (本例中是 `name`)

    `__getattr__` 的使用方式: 当任何正常途径无法访问属性时, 会调用此方法.
    详细参考: https://stackoverflow.com/questions/3278077/difference-between-getattr-vs-getattribute
    """

    def __init__(self, real):
        self.real = real

    def __getattr__(self, name):
        return getattr(self.real, name)

    @property
    def name(self):
        return 'mock'
