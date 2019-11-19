__all__ = (
    'CaseInsensitiveDict',
)

from collections import UserDict


class CaseInsensitiveDict(UserDict):
    """无视大小写的 dict

    实际上真正使用时可以用 requests.structures.CaseInsensitiveDict.

    可作为其他自定义 dict 的参考, 主要需要 override 下面四个方法:

    - __setitem__
    - __getitem__
    - __delitem__

    get, __contains__ 方法会调用 `__getitem__` 所以不用 override
    """

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __delitem__(self, key):
        super().__delitem__(key.lower())
