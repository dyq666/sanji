__all__ = (
    'Base64',
    'CaseInsensitiveDict',
    'clean_textarea',
    'fill_sequence',
    'import_object',
    'rm_control_chars',
    'round_half_up',
    'sequence_grouper',
    'write_csv',
)

import base64
import csv
import math
import re
from collections import UserDict
from decimal import ROUND_HALF_UP, Decimal
from importlib import import_module
from io import StringIO
from typing import (
    Any, Iterable, List, Optional, Tuple, Union,
)

Col = Union[list, tuple]  # Collection
Number = Union[int, float]
Seq = Union[list, tuple, str, bytes]
Text = Union[str, bytes]


class Base64:
    """可选择是否填充等号的 Base64"""

    @staticmethod
    def b64encode(s: bytes, with_equal: bool = False) -> bytes:
        content = base64.b64encode(s)
        if with_equal:
            content = content.rstrip(b'=')
        return content

    @staticmethod
    def b64decode(s: bytes, with_equal: bool = False) -> bytes:
        if with_equal:
            s = fill_sequence(s, 4, b'=')
        return base64.b64decode(s)

    @staticmethod
    def urlsafe_b64encode(s: bytes, with_equal: bool = False) -> bytes:
        content = base64.urlsafe_b64encode(s)
        if with_equal:
            content = content.rstrip(b'=')
        return content

    @staticmethod
    def urlsafe_b64decode(s: bytes, with_equal: bool = False) -> bytes:
        if with_equal:
            s = fill_sequence(s, 4, b'=')
        return base64.urlsafe_b64decode(s)


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


def clean_textarea(value: str, keep_inline_space: bool = True
                   ) -> Union[List[str], List[List[str]]]:
    """在字符串中获取数据.

    keep_inline_space: 是否拆分一行中的数据
    """
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def fill_sequence(sequence: Seq, size: int, filler: Any) -> Seq:
    if not isinstance(sequence, (str, bytes, list, tuple)):
        raise TypeError
    if len(sequence) % size == 0:
        return sequence

    filler_number = size - (len(sequence) % size)
    if isinstance(sequence, (str, bytes)):
        return sequence + filler * filler_number
    elif isinstance(sequence, (list, tuple)):
        return sequence + type(sequence)(filler for _ in range(filler_number))


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


def sequence_grouper(sequence: Seq, size: int,
                     filler: Optional[Any] = None) -> Iterable:
    """按组迭代, 如果 default is not None 则会用 size 个 default 补齐最后一组"""
    if not isinstance(sequence, (str, bytes, list, tuple)):
        raise TypeError

    times = math.ceil(len(sequence) / size)
    for i in range(times):
        item = sequence[i * size: (i + 1) * size]
        if filler is not None:
            missing_number = size - len(item)
            if isinstance(sequence, (str, bytes)):
                item += filler * missing_number
            elif isinstance(sequence, (list, tuple)):
                item += type(sequence)(filler for _ in range(missing_number))
            yield item
        else:
            yield item


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
