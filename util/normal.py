__all__ = (
    'CSV', 'Base64', 'Binary', 'BitField', 'DefaultDict',
    'KindTree', 'PrioQueue', 'Version', 'accessors', 'camel2snake',
    'chinese_num', 'format_rows', 'fill_seq', 'merge_sorted_list',
    'no_value',
    'import_object', 'indent_data', 'percentage',
    'rm_around_space', 'round_half_up', 'seq_grouper',
    'strip_control', 'strip_seq',
)

import base64
import binascii
import csv
import enum
import heapq
import importlib
import inspect
import io
import json
import operator
import re
import struct
from collections import UserDict, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from functools import reduce, partial, total_ordering
from typing import (
    Any, Iterable, List, Generator, Optional, Sequence,
    Set, Tuple, Union,
)

BuiltinSeq = Union[bytes, list, str, tuple]
BuiltinNum = Union[int, float]

no_value = object()


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
        return cls(reduce(operator.or_, ids))


class DefaultDict(UserDict):

    def __init__(self, default: Any, *args, **kwargs):
        self.default = default
        super().__init__(*args, **kwargs)

    def __missing__(self, key):
        return self.default


class KindTree:
    """种类树.

    用于有从属关系但不需要动态变化的数据, 例如一个常用功能 - 分类.
    由于是静态的, 初始化时就计算了所有父节点和所有子节点, 牺牲空间减少运行时的计算时间.
    """

    def __init__(self, values: Tuple[Tuple[str, Optional[str], str, Optional[str]], ...]):
        data1 = {}
        # 先记下所有的常量名, 下面再转为实例常量.
        consts = {}
        for id_, parent_id, name, const in values:
            if id_ in data1:
                raise ValueError
            data1[id_] = {
                'id': id_,
                'parent_id': parent_id,
                'name': name,
            }
            if const is not None:
                consts[id_] = const

        data2 = {}
        childs = defaultdict(set)
        for id_, datum in data1.items():
            # 找到节点的所有父节点.
            parent_ids = []
            parent_id = datum['parent_id']
            while parent_id is not None:
                parent_ids.append(parent_id)
                # 记录子节点.
                childs[parent_id].add(id_)
                parent_id = data1[parent_id]['parent_id']
            # 根据所有父节点计算父节点和根节点.
            if len(parent_ids) == 0:
                root_id = None
                parent_id = None
            else:
                root_id = parent_ids[-1]
                parent_id = parent_ids[0]

            data2[id_] = {
                'id': datum['id'],
                'parent_id': parent_id,
                'root_id': root_id,
                'parent_ids': parent_ids,
                'name': datum['name'],
            }

        nodes = {}
        for id_, datum in data2.items():
            kind = KindNode(
                id_=datum['id'],
                parent_id=datum['parent_id'],
                root_id=datum['root_id'],
                parent_ids=datum['parent_ids'],
                child_ids=childs[id_],
                name=datum['name'],
                tree=self,
            )
            nodes[id_] = kind
            # 设置常量.
            if id_ in consts:
                setattr(self, consts[id_], kind)
        self.nodes = nodes

    def __iter__(self) -> Iterable['KindNode']:
        return iter(self.nodes.values())

    def get(self, kind_id: str) -> Optional['KindNode']:
        return self.nodes.get(kind_id)

    def gets(self, kind_ids: Union[Tuple[str, ...], List[str]]) -> List['KindNode']:
        return [kind for id_ in kind_ids if (kind := self.nodes.get(id_)) is not None]


class KindNode:
    """种类树的每个节点."""

    def __init__(self, id_: str, parent_id: Optional[str],
                 root_id: Optional[str], parent_ids: List[str],
                 child_ids: Set[str], name: str, tree: 'KindTree'):
        self.id = id_
        self.parent_id = parent_id
        self.root_id = root_id
        self.parent_ids = parent_ids  # 从子节点到父节点
        self.child_ids = child_ids  # 无顺序
        self.name = name
        self.tree = tree

    def __repr__(self):
        return (
            f'<{self.__class__.__name__}'
            f' id={self.id!r}'
            f' parent_id={self.parent_id!r}'
            f' root_id={self.root_id!r}'
            f' elder_ids={self.parent_ids!r}'
            f' name={self.name!r}'
            f'>'
        )

    @property
    def parent(self) -> Optional['KindNode']:
        return self.tree.get(self.parent_id)

    @property
    def root(self) -> Optional['KindNode']:
        return self.tree.get(self.root_id)


class PrioQueue:
    """PriorityQueue, 优先级队列.

    和 `queue.PriorityQueue` 的区别:

      1. 内置一个 `index` 使得当 `priority` 相同时, 仍可比较.
      2. 参数 `asc` 决定先返回优先级小的还是大的, 默认先返回小的.
      3. `get` 时只返回 `item`.
    """

    def __init__(self, asc: bool = True):
        self._heap = []
        self._index = 0
        self._asc = asc

    def __len__(self) -> int:
        return len(self._heap)

    def put(self, priority: int, item: Any):
        priority = priority if self._asc else -priority
        heapq.heappush(self._heap, (priority, self._index, item))
        self._index += 1

    def get(self):
        return heapq.heappop(self._heap)[-1]

    @classmethod
    def from_pairs(cls, pairs: Iterable[Tuple[int, Any]],
                   asc: bool = True) -> 'PrioQueue':
        q = cls(asc)
        for priority, item in pairs:
            q.put(priority, item)
        return q


@total_ordering
class Version:

    def __init__(self, major: int, minor: int, revision: int):
        self.major = major
        self.minor = minor
        self.revision = revision

    def __repr__(self):
        return (
            f'<{self.__class__.__name__}'
            f' major={self.major!r}'
            f' minor={self.minor!r}'
            f' revision={self.revision!r}'
            f'>'
        )

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.revision}'

    def __eq__(self, other: 'Version'):
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.revision == other.revision
        )

    def __gt__(self, other: 'Version'):
        # 前一级版本号相等时, 再比后一级版本号.
        res = (
            self.major - other.major
            or self.minor - other.minor
            or self.revision - other.revision
        )
        return res > 0

    @classmethod
    def parse(cls, version_str: str) -> Optional['Version']:
        if not version_str:
            return

        group = [int(i) for i in version_str.split('.')]
        group = fill_seq(group, size=3, filler=0)
        return Version(*group)


def accessors(enum_cls: enum.Enum, cls_func_name: str,
              cls_property_prefix: str = 'is_') -> callable:
    """批量给类增加 `property`, 用于便捷访问某种已有的属性.

    `enum_cls`: 提供一组常量, 常量名将转化为新属性名的一部分, 常量值将作为新属性的参数.
    `cls_func_name`: 类中已有的函数, 将作为新属性实际执行的逻辑 (func body).
    `cls_property_prefix`: 新属性名的前缀.
    """
    def deco(cls: type):
        func = getattr(cls, cls_func_name)
        # 由于 `func` 是一个 method, 所以获取函数的第二个参数名用于下面的 `partial`, 避开 `self` 参数.
        param_name = list(inspect.signature(func).parameters.keys())[1]

        for name, value in enum_cls.__members__.items():
            property_name = cls_property_prefix + name.lower()
            if property_name in cls.__dict__:
                raise ValueError
            property_method = property(partial(func, **{param_name: value}))
            # 注意这里不能使用 `partialmethod`, 它不是 `callable`.
            setattr(cls, property_name, property_method)

        return cls
    return deco


def camel2snake(s: str) -> str:
    """camel case 转 snake case.

    首字母必须是大写.

    更好的方案应该是: peewee.py::make_snake_case.
    """
    if not s:
        return ''
    if not s[0].isupper():
        raise ValueError

    items = re.findall(r'[A-Z][_a-z]*', s)
    return '_'.join(item for item in items).lower()


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


def fill_seq(seq: BuiltinSeq, size: int, filler: Any) -> BuiltinSeq:
    """用 `filler` 填充序列使其能被 `size` 整除."""
    if isinstance(seq, (str, bytes)) and len(filler) != 1:
        raise ValueError

    if len(seq) % size == 0:
        return seq

    num = size - (len(seq) % size)
    if isinstance(seq, (str, bytes)):
        return seq + filler * num
    else:  # list or tuple
        return seq + type(seq)(filler for _ in range(num))


def format_rows(data: List[dict]) -> str:
    """用更可读的形式展示数据."""
    # 计算每列的最大长度.
    lens = defaultdict(int)
    for row in data:
        for k, v in row.items():
            lens[k] = max(len(str(v)), lens[k])
    lens = {k: max(len(k), v) for k, v in lens.items()}

    # header
    res = [
        '  '.join('{:<{}}'.format(k, v) for k, v in lens.items()),
        '  '.join('{:<{}}'.format('-' * v, v) for v in lens.values()),
    ]

    # data
    for row in data:
        s = '  '.join('{:<{}}'.format(str(v), lens[k]) for k, v in row.items())
        res.append(s)
    return '\n'.join(res)


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


def indent_data(data: Union[list, tuple, dict], show_unicode: bool = True) -> str:
    """将数据转换成四空格缩进的格式.

    `show_unicode`: 是否转化为 Python 中 unicode.

    参考:
        https://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python/4020824#4020824
    """
    data = json.dumps(data, indent=4)
    if show_unicode:
        data = data.encode().decode('unicode_escape')
    return data


def merge_sorted_list(a1: list, a2: list) -> Iterable:
    """合并两个有序列表."""
    idx1, idx2 = 0, 0

    for _ in range(len(a1) + len(a2)):
        # 如果某个数组遍历结束了, 就用无穷大代替当前数组的值.
        v1 = a1[idx1] if idx1 < len(a1) else float('inf')
        v2 = a2[idx2] if idx2 < len(a2) else float('inf')
        if v1 < v2:
            idx1 += 1
        else:
            idx2 += 1
        yield min(v1, v2)


def percentage(molecule: BuiltinNum, denominator: BuiltinNum, with_format: bool = True
               ) -> Union[str, float]:
    # 分母不能为 0
    res = 0.0 if not denominator else molecule * 100 / denominator

    if not with_format:
        return res
    return f'{res:.2f}%'


def rm_around_space(value: str, keep_inline_space: bool = True
                    ) -> Union[List[str], List[List[str]]]:
    """清除字符串上下左右的空白字符.

    `keep_inline_space`: 是否保留行内的空白字符
    """
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def round_half_up(number: BuiltinNum, ndigits: int = 0) -> BuiltinNum:
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


def seq_grouper(seq: BuiltinSeq, size: int,
                filler: Any = no_value) -> Generator:
    """按组迭代序列.

    `size`: 每组的大小.
    `filler`: 如果传入, 则用此值填充最后一组.
    """
    if filler is not no_value:
        seq = fill_seq(seq, size, filler)
    return (seq[i: i + size] for i in range(0, len(seq), size))


def strip_control(value: str) -> str:
    """去除字符串中的控制字符."""
    control_chars_reg = r'[\x00-\x1f\x7f]'
    return re.sub(control_chars_reg, '', value)


def strip_seq(seq: Sequence, size: int) -> Sequence:
    """从末尾移除序列使其能被 `size` 整除."""
    remainder = len(seq) % size
    end = -remainder if remainder else None
    return seq[:end]
