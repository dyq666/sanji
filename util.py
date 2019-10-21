__all__ = (
    'CaseInsensitiveDict',
    'Memoize',
    'clean_textarea',
    'fill_str',
    'import_object',
    'rm_control_chars',
    'round_half_up',
    'sequence_grouper',
    'write_csv',
)

import csv
import math
import re
from collections import UserDict
from decimal import ROUND_HALF_UP, Decimal
from importlib import import_module
from io import StringIO
from typing import (
    Any, Iterable, List, Optional, Sequence, Tuple, Union,
)

Number = Union[int, float]


class CaseInsensitiveDict(UserDict):
    """无视大小写的 DICT

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


class Memoize:
    """缓存属性.

    类似 property, 区别是 memoize 的属性只会计算一次.
    需要注意的是类中不应该有和 `self.cache_key` 相同的属性.
    """

    def __init__(self, fget):
        self.fget = fget
        # property 也设置了 __doc__.
        self.__doc__ = fget.__doc__
        self.cache_key = '__cache_' + fget.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if not hasattr(instance, self.cache_key):
            setattr(instance, self.cache_key, self.fget(instance))
        return getattr(instance, self.cache_key)


def clean_textarea(value: str, keep_inline_space: bool = True
                   ) -> Union[List[str], List[List[str]]]:
    """在字符串中获取数据.

    keep_inline_space: 是否拆分一行中的数据
    """
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def fill_str(str_: str, number: int, filler: str) -> str:
    """填充字符串是它的长度可以被某个数整除

    为什么有这个看起来很简单的方法呢 ? 在脑子不转的情况下会忘记 == 0 的情况 ...
    """
    if len(str_) % number == 0:
        return str_

    return str_ + filler * (number - len(str_) % number)


def import_object(object_path: str) -> Any:
    try:
        dot = object_path.rindex('.')
        module, obj = object_path[:dot], object_path[dot + 1:]
        return getattr(import_module(module), obj)
    # rindex        -> ValueError
    # import_module -> ModuleNotFoundError
    # getattr       -> AttributeError
    except (ValueError, ModuleNotFoundError, AttributeError):
        raise ImportError(f'Cannot import {object_path}')


def rm_control_chars(str_: str) -> str:
    control_chars_reg = r'[\x00-\x1f\x7f]'
    return re.sub(control_chars_reg, '', str_)


def round_half_up(number: Number, ndigits: int = 0) -> Number:
    """四舍五入.

    ndigits: 与 ``round`` 的参数 ``ndigits`` 保持一样的逻辑:
             > 0 小数位, <= 0 整数位.
    """
    def _get_number(_ndigits: int) -> int:
        return int(str(number)[_ndigits - 1])

    if ndigits <= 0:
        half_even_result = int(round(number, ndigits))

        # 如果保留位是偶数 & 保留位后一位是 5 & 5 后面全是 0, 那么就入
        if all((
            _get_number(ndigits) & 1 == 0,
            _get_number(ndigits + 1) == 5,
            number % (10 ** abs(ndigits + 1)) == 0
        )):
            return half_even_result + 10 ** abs(ndigits)
        return half_even_result

    decimal = Decimal(str(number))
    position = Decimal('0.{}1'.format('0' * (abs(ndigits) - 1)))
    return float(decimal.quantize(position, rounding=ROUND_HALF_UP))


def sequence_grouper(sequence: Sequence, size: int) -> Iterable:
    """按组迭代"""
    times = math.ceil(len(sequence) / size)
    return (sequence[i * size: (i + 1) * size] for i in range(times))


def write_csv(header: Tuple[str, ...],
              rows: Union[Tuple[dict, ...], Tuple[list, ...], Tuple[tuple, ...]],
              file_path: Optional[str] = None
              ) -> Optional[StringIO]:
    """将数据写入 csv

    header: 标题

    rows: 数据行

    file_path: 不传会返回一个 StringIO, 传则写入此路径.
    """
    if not header or not rows:
        raise ValueError('header or rows should not empty')
    if not isinstance(rows[0], (dict, list, tuple)):
        raise TypeError('type of row item must be dict or tuple or list')

    file = StringIO() if file_path is None else open(file_path, 'w')

    if isinstance(rows[0], dict):
        f_csv = csv.DictWriter(file, header)
        f_csv.writeheader()
        f_csv.writerows(rows)
    else:
        f_csv = csv.writer(file)
        f_csv.writerow(header)
        f_csv.writerows(rows)

    if file_path is None:
        file.seek(0)
        return file
    else:
        file.close()
        return
