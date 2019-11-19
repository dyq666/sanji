__all__ = (
    'CaseInsensitiveDict',
)

from collections import UserDict


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
