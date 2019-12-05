__all__ = (
    'CSV',
    'Base64',
    'Binary',
    'BitField',
    'chinese_num',
    'fill_seq',
    'import_object',
    'indent_data',
    'round_half_up',
    'seq_grouper',
    'strip_blank',
    'strip_control',
    'strip_seq',
)

import base64
import binascii
import csv
import importlib
import io
import json
import math
import re
import struct
from decimal import ROUND_HALF_UP, Decimal
from functools import reduce
from operator import or_
from typing import (
    Any, Iterable, List, Optional, Tuple, Union,
)

Col = Union[list, tuple, dict]
Num = Union[int, float]
Seq = Union[list, tuple, str, bytes]


class CSV:

    @staticmethod
    def read(filepath: Union[str, io.StringIO], with_dict: bool = False) -> Tuple[list, list]:
        """从文件中读取 csv 格式的数据.

        `with_dict`: 返回的 `rows` 中的数据项类型是否为 `dict` ?
        `file_path`: 如果传入字符串, 那么从此文件路径中读取数据, 否则从 `io.StringIO` 对象中读取数据.
        """
        file = open(filepath, newline='') if isinstance(filepath, str) else filepath

        if with_dict:
            f_csv = csv.DictReader(file)
            rows = list(f_csv)
            header = f_csv.fieldnames
        else:
            f_csv = csv.reader(file)
            header = next(f_csv)
            rows = list(f_csv)

        if isinstance(filepath, str):
            file.close()

        return header, rows

    @staticmethod
    def write(header: Iterable[str], rows: Iterable[Iterable], filepath: Optional[str] = None,
              with_dict: bool = False) -> Optional[io.StringIO]:
        """将数据按 csv 格式写入文件.

        `with_dict`: `rows` 中的数据项类型是否为 `dict` ?
        `file_path`: 如果传入字符串, 那么将数据写入此文件路径, 否则返回 `io.StringIO` 对象.
        """
        file = io.StringIO() if filepath is None else open(filepath, 'w', newline='')

        if with_dict:
            f_csv = csv.DictWriter(file, header)
            f_csv.writeheader()
            f_csv.writerows(rows)
        else:
            f_csv = csv.writer(file)
            f_csv.writerow(header)
            f_csv.writerows(rows)

        if filepath is None:
            file.seek(0)
            return file
        else:
            file.close()
            return


class Base64:
    """可选择是否填充等号的 Base64."""

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


class Binary:

    xor_map = {
        ('0', '0'): '0',
        ('0', '1'): '1',
        ('1', '0'): '1',
        ('1', '1'): '0',
    }

    @classmethod
    def str_xor(cls, s1: str, s2: str) -> str:
        """XOR 两个 8 位二进制字符串."""
        if len(s1) != len(s2):
            raise ValueError

        return ''.join(cls.xor_map[item] for item in zip(s1, s2))

    @classmethod
    def bytes_xor(cls, b1: bytes, b2: bytes) -> bytes:
        """XOR 两个字节序列."""
        return bytes(item1 ^ item2 for item1, item2 in zip(b1, b2))

    @classmethod
    def str_2_bytes(cls, s: str) -> bytes:
        """将 8 位二进制字符串转为字节序列."""
        if len(s) % 8 != 0:
            raise ValueError

        return bytes(cls.str_2_int(item) for item in seq_grouper(s, 8))

    @classmethod
    def hexstr_2_bytes(cls, s: str) -> bytes:
        """将 2 位十六进制字符串转为字节序列."""
        try:
            return binascii.a2b_hex(s)
        except binascii.Error:
            # `if len(s) % 2 != 0` will raise `binascii.Error`
            raise ValueError

    @classmethod
    def bytes_2_str(cls, b: bytes) -> str:
        """将字节序列转为 8 位二进制字符串."""
        return ''.join(cls.int_2_str(byte) for byte in b)

    @classmethod
    def bytes_2_hexstr(cls, b: bytes) -> str:
        """将字节序列转为 2 位十六进制字符串."""
        return binascii.b2a_hex(b).decode()

    @staticmethod
    def bytes_2_int(b: bytes) -> int:
        """将长度为一的 bytes 转成 int."""
        if len(b) != 1:
            raise ValueError

        return struct.unpack('>B', b)[0]

    @staticmethod
    def int_2_str(i: int) -> str:
        """将 [0, 255] 之间的整数转为 1 字节的 8 位二进制字符串."""
        if not 0 <= i <= 255:
            raise ValueError

        return format(i, '08b')

    @staticmethod
    def int_2_hexstr(i: int) -> str:
        """将 [0, 255] 之间的整数转为 1 字节的 2 位十六进制字符串."""
        if not 0 <= i <= 255:
            raise ValueError

        return format(i, '02x')

    @staticmethod
    def int_2_bytes(i: int) -> bytes:
        """将 [0, 255] 之间的整数转为 bytes."""
        if not 0 <= i <= 255:
            raise ValueError

        return struct.pack('>B', i)

    @staticmethod
    def str_2_int(s: str) -> int:
        """将 1 字节的 8 位二进制字符串转为整数."""
        if len(s) != 8:
            raise ValueError

        return int(s, 2)

    @staticmethod
    def hexstr_2_int(s: str) -> int:
        """将 1 字节的 2 位十六进制字符串转为整数."""
        if len(s) != 2:
            raise ValueError

        return int(s, 16)


class BitField:
    """二进制字段.

    '|'
    0 0 -> 0
    0 1 -> 1
    1 0 -> 1
    1 1 -> 1

    '&'
    0 0 -> 0
    0 1 -> 0
    1 0 -> 0
    1 1 -> 1

    '^'
    0 0 -> 0
    0 1 -> 1
    1 0 -> 1
    1 1 -> 0

    上面总共三种操作符, 三列数据, 假设第一列为原始数据, 第二列为操作值, 第三列为最终数据.

    1. 我们希望将 10101 的第四位变为 1, 其他位置不变.
    这时我们选择 '|', 在操作表中观察到操作值 0 不会改变原始数据, 而操作值 1 无论什么情况
    都会让最终数据变为 1. 因此我们需要生成操作值 01000, 而 1000 = 1 << 3.

    2. 我们希望将 10101 的第三位变为 0, 其他位置不变.
    这时我们选择 '&', 在操作表中观察到操作值 0 不会改变原始数据, 而操作值 1 无论什么情况
    都会让最终数据变为 0. 因此我们需要生成操作值 11011, 而 11011 = ~100 = ~(1 << 2).

    3, 我们希望查询 10101 的第三位是否为 1.
    10101 & 00100 = 00100
    10001 & 00100 = 00000
    因此可以得出结论, 如果 > 0 则是 1, 等于 0 则是 0.

    实际上 1-3 的例子分别对应增删查.

    ## 一些其他相关的二进制操作.

    1. 左移, 右移.
    二进制左移等于 * 2
    二进制右移等于 // 2 (如果最后一位是 1, 会被丢弃, 因此是 //)
    ```
    assert 1 << 100 == 1 * (2 ** 100)
    assert 15 >> 1 == 15 // (2 ** 1)
    assert 15 >> 2 == 15 // (2 ** 2)
    assert bin(int('0b1111', 2) >> 1) == '0b111'
    assert bin(int('0b1111', 2) >> 2) == '0b11'
    assert bin(int('0b111', 2) << 1) == '0b1110'
    assert bin(int('0b11', 2) << 2) == '0b1100'
    ```

    2. 取反
    ```
    # Python 中没有符号位使用 '-' 号表示.
    # 补码计算规则: 正数的补码等于原码, 负数的补码等于原码逐位取反 (符号位不取反), 末位 + 1.
    #         计算补码         按位取反        转为原码
    # 01000    ->      01000    ->   10111    ->     11001 (末位 - 1, 逐位取反)
    # 11110    ->      10010    ->   01101    ->     01101
    assert ~8 == -9
    assert ~-8 == 7
    assert ~int('1000', 2) == int('-1001', 2)
    assert ~int('-1110', 2) == int('1101', 2)
    ```
    """

    def __init__(self, ids: int):
        self.ids = ids

    def add(self, value: int):
        self.ids |= value

    def remove(self, value: int):
        self.ids &= ~value

    def has(self, value: int):
        return bool(self.ids & value)

    @classmethod
    def create(cls, ids: Iterable[int]) -> 'BitField':
        return cls(reduce(or_, ids))


def chinese_num(num: int) -> str:
    """将数字转成中文."""
    if num >= 100 or num < 0:
        return ''

    single = dict(zip(
        range(1, 11),
        '一二三四五六七八九十',
    ))
    single[0] = ''

    if num == 0:
        return '零'
    elif num < 11:
        return single[num]
    elif num < 20:
        return single[10] + single[num % 10]
    else:
        return single[num // 10] + single[10] + single[num % 10]


def fill_seq(seq: Seq, size: int, filler: Any) -> Seq:
    """用 `filler` 填充序列使其能被 `size` 整除."""
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
    """根据路径获取对象."""
    try:
        dot = object_path.rindex('.')
        module, obj = object_path[:dot], object_path[dot + 1:]
        return getattr(importlib.import_module(module), obj)
    # rindex        -> ValueError
    # import_module -> ModuleNotFoundError
    # getattr       -> AttributeError
    except (ValueError, ModuleNotFoundError, AttributeError):
        raise ImportError(f'Cannot import {object_path}')


def indent_data(data: Col, show_unicode: bool = True) -> str:
    """将数据转换成四空格缩进的格式.

    `show_unicode`: 是否转化为 Python 中 unicode.

    参考:
        https://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python/4020824#4020824
    """
    data = json.dumps(data, indent=4)
    if show_unicode:
        data = data.encode().decode('unicode_escape')
    return data


def round_half_up(number: Num, ndigits: int = 0) -> Num:
    """四舍五入.

    `ndigits`: 与 ``round`` 的参数 ``ndigits`` 保持一样的逻辑:
               > 0 为修约到小数位, <= 0 为修约到整数位.

    此外:
      大多数真实场景中不需要支持 `ndigits <= 0` 的情况, 因此只需要复制最后三行即可.
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

    `size`: 每组的大小.
    `filler`: 如果传入, 则用此值填充最后一组.
    """
    if not isinstance(seq, (str, bytes, list, tuple)):
        raise TypeError

    if filler is not None:
        seq = fill_seq(seq, size, filler)
    times = math.ceil(len(seq) / size)
    return (seq[i * size: (i + 1) * size] for i in range(times))


def strip_blank(value: str, keep_inline_space: bool = True
                ) -> Union[List[str], List[List[str]]]:
    """在字符串中获取数据.

    `keep_inline_space`: 是否拆分一行中的数据
    """
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def strip_control(value: str) -> str:
    """去除字符串中的控制字符."""
    control_chars_reg = r'[\x00-\x1f\x7f]'
    return re.sub(control_chars_reg, '', value)


def strip_seq(seq: Seq, size: int) -> Seq:
    """从末尾移除序列使其能被 `size` 整除."""
    if not isinstance(seq, (str, bytes, list, tuple)):
        raise TypeError

    if len(seq) % size == 0:
        return seq

    num = len(seq) % size
    return seq[:-num]
