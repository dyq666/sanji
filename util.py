__all__ = (
    'Base64',
    'CaseInsensitiveDict',
    'clean_textarea',
    'fill_seq',
    'import_object',
    'rm_control_chars',
    'round_half_up',
    'seq_grouper',
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
Num = Union[int, float]
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
            s = fill_seq(s, 4, b'=')
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
            s = fill_seq(s, 4, b'=')
        return base64.urlsafe_b64decode(s)


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


def clean_textarea(value: str, keep_inline_space: bool = True
                   ) -> Union[List[str], List[List[str]]]:
    """在字符串中获取数据.

    keep_inline_space: 是否拆分一行中的数据
    """
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def fill_seq(seq: Seq, size: int, filler: Any) -> Seq:
    """用 `filler` 填充序列使其内被 `size` 整除"""
    if not isinstance(seq, (str, bytes, list, tuple)):
        raise TypeError
    if len(seq) % size == 0:
        return seq

    num = size - (len(seq) % size)
    if isinstance(seq, (str, bytes)):
        return seq + filler * num
    else:  # list or tuple
        return seq + type(seq)(filler for _ in range(num))


def import_object(object_path: str) -> Any:
    """根据路径获取对象"""
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
    """去除控制字符"""
    control_chars_reg = r'[\x00-\x1f\x7f]'
    return re.sub(control_chars_reg, '', str_)


def round_half_up(number: Num, ndigits: int = 0) -> Num:
    """四舍五入.

    ndigits: 与 ``round`` 的参数 ``ndigits`` 保持一样的逻辑:
             > 0 小数位, <= 0 整数位.

    实际上大多数场景不需要支持 `ndigits <= 0` 的情况.
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


def seq_grouper(seq: Seq, size: int, filler: Optional[Any] = None) -> Iterable:
    """按组迭代序列.

    如果传入了 `filler` 则会用 `filler` 填充最后一组, 使之可以被 `size` 整除.
    """
    if not isinstance(seq, (str, bytes, list, tuple)):
        raise TypeError

    if filler is not None:
        seq = fill_seq(seq, size, filler)
    times = math.ceil(len(seq) / size)
    yield from (seq[i * size: (i + 1) * size] for i in range(times))


def write_csv(header: Tuple[str, ...],
              rows: Union[Tuple[dict, ...], Tuple[list, ...], Tuple[tuple, ...]],
              file_path: Optional[str] = None
              ) -> Optional[StringIO]:
    """将数据写入 csv

    如果传 `file_path` 则将数据写入此路径, 否则返回 StringIO
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
