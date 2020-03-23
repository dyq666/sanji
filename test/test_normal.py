import enum
import os
import tempfile
from functools import partial

import pytest

from util import (
    CSV, Base64, Binary, BitField, DefaultDict,
    KindTree, PrioQueue, Version, accessors,
    camel2snake, chinese_num, format_rows,
    fill_seq, import_object, indent_data, merge_sorted_list,
    percentage, rm_around_space,
    round_half_up, seq_grouper,
    strip_control, strip_seq,
)


class TestCSV:

    header = ['name', 'sex']
    rows = [['father', 'male'], ['mother', 'female']]
    content = 'name,sex\nfather,male\nmother,female\n'

    @property
    def dict_rows(self):
        return [dict(zip(self.header, row)) for row in self.rows]

    @pytest.fixture
    def types_group(self) -> tuple:
        return (
            [self.rows, False],
            [self.dict_rows, True],
        )

    def test_write_with_path(self, types_group):
        with tempfile.TemporaryDirectory() as dirname:
            filepath = os.path.join(dirname, 'data.csv')
            for rows, with_dict in types_group:
                CSV.write(self.header, rows, with_dict=with_dict, filepath=filepath)

                with open(filepath) as f:
                    assert f.read() == self.content

    def test_write_without_path(self, types_group):
        for rows, with_dict in types_group:
            file = CSV.write(self.header, rows, with_dict=with_dict)
            assert file.getvalue().replace('\r\n', '\n') == self.content

    def test_read_with_path(self):
        with tempfile.TemporaryDirectory() as dirpath:
            filepath = os.path.join(dirpath, 'data.csv')
            CSV.write(self.header, self.rows, filepath=filepath)

            assert CSV.read(filepath) == (self.header, self.rows)
            assert CSV.read(filepath, with_dict=True) == (self.header, self.dict_rows)

    def test_read_without_path(self):
        f = CSV.write(self.header, self.rows)
        assert CSV.read(f) == (self.header, self.rows)
        f.seek(0)
        assert CSV.read(f, with_dict=True) == (self.header, self.dict_rows)


class TestBase64:
    """= 号只有三种情况, 两个, 一个, 零个. 因此只用选三个特例就行."""

    @pytest.mark.parametrize('func', (Base64.b64encode, Base64.urlsafe_b64encode))
    def test_strip_equal(self, func):
        encode1 = partial(func, with_equal=True)
        encode2 = partial(func, with_equal=False)
        assert encode1(b'a') == encode2(b'a')[:-2]
        assert encode1(b'aa') == encode2(b'aa')[:-1]
        assert encode1(b'aaa') == encode2(b'aaa')

    @pytest.mark.parametrize('with_equal', (True, False))
    @pytest.mark.parametrize('funcs', (
        [Base64.b64encode, Base64.b64decode],
        [Base64.urlsafe_b64encode, Base64.urlsafe_b64decode],
    ))
    def test_encode_and_decode(self, with_equal, funcs):
        encode = partial(funcs[0], with_equal=with_equal)
        decode = partial(funcs[1], with_equal=with_equal)
        assert decode(encode(b'a')) == b'a'
        assert decode(encode(b'aa')) == b'aa'
        assert decode(encode(b'aaa')) == b'aaa'


class TestBinary:

    def test_int_2_bytes(self):
        with pytest.raises(ValueError):
            Binary.int_2_bytes(-1)
        with pytest.raises(ValueError):
            Binary.int_2_bytes(256)

        assert Binary.int_2_bytes(0) == b'\x00'
        assert Binary.int_2_bytes(255) == b'\xff'

    def test_bytes_2_int(self):
        with pytest.raises(ValueError):
            Binary.bytes_2_int(b'\x00\xff')

        assert Binary.bytes_2_int(b'\x00') == 0
        assert Binary.bytes_2_int(b'\xff') == 255

    def test_str_xor(self):
        with pytest.raises(KeyError):
            Binary.str_xor('1', '2')

        with pytest.raises(ValueError):
            Binary.str_xor('11', '000')

        assert Binary.str_xor('0011', '0101') == '0110'

    def test_bytes_xor(self):
        assert Binary.bytes_xor(b'\x03', b'\x05') == b'\x06'

    def test_str_2_bytes(self):
        with pytest.raises(ValueError):
            Binary.str_2_bytes('11')

        s = ''.join(['00001100', '00100001'])
        assert Binary.str_2_bytes(s) == bytes([12, 33])

    def test_hexstr_2_bytes(self):
        with pytest.raises(ValueError):
            Binary.hexstr_2_bytes('f')

        s = ''.join(['0C', '21'])
        assert Binary.hexstr_2_bytes(s) == bytes([12, 33])

    def test_bytes_2_str(self):
        assert Binary.bytes_2_str(b'\x00\x01\xff') == ''.join(['00000000', '00000001', '11111111'])

    def test_bytes_2_hexstr(self):
        assert Binary.bytes_2_hexstr(b'\x00\x01\xff') == ''.join(['00', '01', 'ff'])

    def test_int_2_str(self):
        assert Binary.int_2_str(255) == '11111111'
        assert Binary.int_2_str(0) == '00000000'

        with pytest.raises(ValueError):
            Binary.int_2_str(-1)

        with pytest.raises(ValueError):
            Binary.int_2_str(256)

    def test_int_2_hexstr(self):
        assert Binary.int_2_hexstr(255) == 'ff'
        assert Binary.int_2_hexstr(0) == '00'

        with pytest.raises(ValueError):
            Binary.int_2_hexstr(-1)

        with pytest.raises(ValueError):
            Binary.int_2_hexstr(256)

    def test_str_2_int(self):
        assert Binary.str_2_int('11111111') == 255
        assert Binary.str_2_int('00000000') == 0

        with pytest.raises(ValueError):
            Binary.str_2_int('111000001111')

        with pytest.raises(ValueError):
            Binary.str_2_int('12345678')

    def test_hexstr_2_int(self):
        assert Binary.hexstr_2_int('ff') == 255
        assert Binary.hexstr_2_int('00') == 0

        with pytest.raises(ValueError):
            Binary.hexstr_2_int('fff')

        with pytest.raises(ValueError):
            Binary.hexstr_2_int('zz')


def test_bit_field():
    @enum.unique
    class ID(enum.IntEnum):
        ANIMAL = 1 << 0
        HUMAN = 1 << 1
        MAMMALIA = 1 << 2
        OTHER = 1 << 3

    ids = (ID.ANIMAL, ID.HUMAN, ID.MAMMALIA)
    bit_field = BitField.create(ids)
    for id_ in ids:
        assert bit_field.has(id_)

    bit_field.remove(ID.ANIMAL)
    assert not bit_field.has(ID.ANIMAL)
    assert bit_field.has(ID.HUMAN)
    assert bit_field.has(ID.MAMMALIA)

    bit_field.add(ID.OTHER)
    assert not bit_field.has(ID.ANIMAL)
    assert bit_field.has(ID.HUMAN)
    assert bit_field.has(ID.MAMMALIA)
    assert bit_field.has(ID.OTHER)


class TestDefaultDict:
    """测试了下面的 11 个字典的方法

    ```
    __getitem__
    __setitem__
    __delitem__
    __len__
    __iter__
    __contains__
    get
    items
    values
    keys
    fromkeys
    ```
    """

    @pytest.fixture
    def d(self):
        return DefaultDict('default')

    def test_get_and_getitem(self, d):
        d['c'] = 2
        assert d.get('c') == 2
        assert d['c'] == 2
        assert d.get('d') == 'default'
        assert d['d'] == 'default'

    def test_setitem_and_len_and_items_and_contains_and_del(self, d):
        """访问不存在的 key 之后, 并不会把此 key 放入字典中."""
        d['c'] = 2
        assert d['d'] == 'default'

        assert 'c' in d
        assert 'd' not in d
        assert dict(d.items()) == {'c': 2}
        assert len(d) == 1

        with pytest.raises(KeyError):
            del d['d']
        del d['c']
        assert len(d) == 0

    def test_keys_and_values_and_iter(self, d):
        keys = ''.join(str(i) for i in range(10))
        d.update(zip(keys, range(10)))
        assert ''.join(d) == keys
        assert ''.join(d.keys()) == keys
        assert list(d.values()) == list(range(10))


class TestKindTree:
    values = (
        ('1', None, '电器', None),
        ('10', '1', '电脑', 'COMPUTER'),
        ('101', '10', '笔记本电脑', None),
        ('102', '10', '台式电脑', None),

        ('2', None, '水果', None),
        ('20', '2', '热带水果', None),
        ('201', '20', '芒果', 'MANGO'),
    )
    ElectricalKind = KindTree(values)

    def test_exception(self):
        with pytest.raises(ValueError):
            KindTree((
                ('1', None, '电器', None),
                ('1', '1', '电脑', 'COMPUTER'),
            ))

    def test_kind_tree_fields(self):
        """测试 `get`, `gets`, `__iter__`."""
        assert self.ElectricalKind.get('1').id == '1'
        assert [k.id for k in self.ElectricalKind.gets(['1', '2', '3', '10'])] == ['1', '2', '10']
        assert [k.id for k in self.ElectricalKind] == ['1', '10', '101', '102',
                                                       '2', '20', '201']

    def test_kind_node_fields(self):
        # 分别测试根节点, 1 级节点, 2级节点.
        kind1 = self.ElectricalKind.get('1')
        assert [kind1.id, kind1.parent_id,
                kind1.root_id, kind1.parent_ids,
                kind1.child_ids,
                kind1.name] == ['1', None, None, [], {'10', '101', '102'}, '电器']
        kind2 = self.ElectricalKind.get('10')
        assert [kind2.id, kind2.parent_id,
                kind2.root_id, kind2.parent_ids,
                kind2.child_ids,
                kind2.name] == ['10', '1', '1', ['1'], {'101', '102'}, '电脑']
        kind3 = self.ElectricalKind.get('101')
        assert [kind3.id, kind3.parent_id,
                kind3.root_id, kind3.parent_ids,
                kind3.child_ids,
                kind3.name] == ['101', '10', '1', ['10', '1'], set(), '笔记本电脑']
        kind4 = self.ElectricalKind.get('2')
        assert [kind4.id, kind4.parent_id,
                kind4.root_id, kind4.parent_ids,
                kind4.child_ids,
                kind4.name] == ['2', None, None, [], {'20', '201'}, '水果']
        kind5 = self.ElectricalKind.get('20')
        assert [kind5.id, kind5.parent_id,
                kind5.root_id, kind5.parent_ids,
                kind5.child_ids,
                kind5.name] == ['20', '2', '2', ['2'], {'201'}, '热带水果']
        kind6 = self.ElectricalKind.get('201')
        assert [kind6.id, kind6.parent_id,
                kind6.root_id, kind6.parent_ids,
                kind6.child_ids,
                kind6.name] == ['201', '20', '2', ['20', '2'], set(), '芒果']

        # 测试常量
        assert self.ElectricalKind.COMPUTER.id == '10'
        assert self.ElectricalKind.MANGO.id == '201'


def test_PrioQueue():
    """
    1. 测试最小优先级队列和最大优先级队列.
    2. 测试相同优先级元素是否能正常比较, 是否按照入队顺序出队.
    """
    # 1
    pairs = [(1, 'a'), (2, 'b')]
    pq = PrioQueue.from_pairs(pairs, asc=True)
    assert pq.pop() == 'a'
    assert pq.pop() == 'b'
    assert len(pq) == 0
    pq = PrioQueue.from_pairs(pairs, asc=False)
    assert pq.pop() == 'b'
    assert pq.pop() == 'a'
    assert len(pq) == 0

    # 2
    class A:
        def __init__(self, val):
            self.val = val

    pq = PrioQueue()
    pq.push(1, A('a'))
    pq.push(2, A('b'))
    assert pq.pop().val == 'a'
    assert pq.pop().val == 'b'
    assert len(pq) == 0


def test_version():
    # 自动补全三位版本号
    assert Version.parse('') is None
    assert str(Version.parse('4')) == '4.0.0'
    assert str(Version.parse('4.0')) == '4.0.0'
    assert str(Version.parse('4.0.0')) == '4.0.0'

    assert Version.parse('4.0.1') >= Version.parse('4.0.1')
    assert Version.parse('4.0.2') >= Version.parse('4.0.1')

    assert Version.parse('4.0.1') <= Version.parse('4.0.1')
    assert Version.parse('4.0.1') <= Version.parse('4.0.2')

    assert Version.parse('10.3.2') > Version.parse('10.2.3')
    assert Version.parse('0') < Version.parse('321.3123.3123')
    assert Version.parse('4') == Version.parse('4.0.0')


class TestAccessors:
    @enum.unique
    class Status(enum.IntEnum):
        DRAFT = 0
        NORMAL = 1
        REJECTED = 2

    @accessors(enum_cls=Status, cls_func_name='_is_status')
    class Contract:

        def __init__(self, status: int):
            self.status = status

        def _is_status(self, status) -> bool:
            return self.status == status

    @accessors(enum_cls=Status, cls_func_name='_is_status',
               cls_property_prefix='has_')
    class Contract2:

        def __init__(self, status: int):
            self.status = status

        def _is_status(self, status) -> bool:
            return self.status == status

    def test_property_prefix(self):
        contract = self.Contract(self.Status.DRAFT)
        assert contract.is_draft is True
        assert contract.is_normal is False
        assert contract.is_rejected is False

        contract2 = self.Contract2(self.Status.NORMAL)
        assert contract2.has_draft is False
        assert contract2.has_normal is True
        assert contract2.has_rejected is False
        with pytest.raises(AttributeError):
            contract2.is_draft

    def test_repeated_property(self):
        with pytest.raises(ValueError):
            @accessors(enum_cls=self.Status, cls_func_name='_is_status')
            class Contract:
                def __init__(self, status: int):
                    self.status = status

                def _is_status(self, status) -> bool:
                    return self.status == status

                @property
                def is_draft(self) -> bool:
                    return self.status == self.Status.DRAFT


def test_camel2snake():
    # test empty
    assert camel2snake('') == ''
    # test exception
    with pytest.raises(ValueError):
        camel2snake('_')
        camel2snake('a')

    assert camel2snake('UserGroup') == 'user_group'


def test_chinese_num():
    fixtures = (
        (0, '零'),
        (1, '一'),
        (9, '九'),
        (10, '十'),
        (11, '十一'),
        (19, '十九'),
        (20, '二十'),
        (29, '二十九'),
        (99, '九十九'),
        # error fixtures
        (-1, ''),
        (100, ''),
    )
    for num, chinese in fixtures:
        assert chinese_num(num) == chinese


def test_format_rows():
    rows = [
        {'cust_name': 'Village Toys',
         'cust_contact': 'John Smith',
         'cust_email': 'sales@villagetoys.com'},
        {'cust_name': 'Fun4All',
         'cust_contact': 'Jim Jones',
         'cust_email': 'jjones@fun4all.com'},
        {'cust_name': 'The Toy Store',
         'cust_contact': 'Kim Howard',
         'cust_email': None}
    ]
    res = format_rows(rows)
    assert res == (
        'cust_name      cust_contact  cust_email           \n'
        '-------------  ------------  ---------------------\n'
        'Village Toys   John Smith    sales@villagetoys.com\n'
        'Fun4All        Jim Jones     jjones@fun4all.com   \n'
        'The Toy Store  Kim Howard    None                 '
    )


class TestFillSeq:

    @pytest.mark.parametrize(('seq', 'filler'), (
        ('', '22'),
        (b'', b'22'),
    ))
    def test_exception(self, seq, filler):
        with pytest.raises(ValueError):
            fill_seq(seq, size=4, filler=filler)

    @pytest.mark.parametrize(('seq', 'filler'), (
        ('', '1'),
        (b'', b'1'),
        ([], 1),
        ((), 1),
    ))
    def test_empty(self, seq, filler):
        assert fill_seq(seq, size=9, filler=filler) == seq

    @pytest.mark.parametrize(('item', 'filler'), (
        ('1', '='),
        (b'1', b'='),
    ))
    def test_text_type_not_empty(self, item, filler):
        for i in range(1, 5):
            seq = item * i
            fillers = filler * (4 - i)
            assert fill_seq(seq, 4, filler) == seq + fillers

    @pytest.mark.parametrize(('cls', 'item', 'filler'), (
        (list, 1, '='),
        (tuple, 2, '='),
    ))
    def test_collection_type_not_empty(self, cls, item, filler):
        for i in range(1, 5):
            seq = cls(item for _ in range(i))
            fillers = cls(filler for _ in range(4 - i))
            assert fill_seq(seq, 4, filler) == seq + fillers


def test_import_object():
    obj = import_object('util.import_object')
    assert obj == import_object

    with pytest.raises(ImportError):
        # ValueError
        import_object('util')
        # ModuleNotFoundError
        import_object('util1.import_object')
        # Attribute
        import_object('util.U')


def test_indent_data():
    data = {'名字': '小红'}
    assert indent_data(data) == (
        '{\n'
        '    "名字": "小红"\n'
        '}'
    )
    assert indent_data(data, show_unicode=False) == (
        '{\n'
        '    "\\u540d\\u5b57": "\\u5c0f\\u7ea2"\n'
        '}'
    )


def test_merge_sorted_list():
    f = merge_sorted_list
    # 列表都为空
    assert list(f([], [])) == []
    # 列表有一个为空
    assert list(f([1], [])) == [1]
    assert list(f([], [1])) == [1]
    # 列表的所有元素都大于或小于另一个列表
    assert list(f([1, 2], [3, 4])) == [1, 2, 3, 4]
    assert list(f([3, 4], [1, 2])) == [1, 2, 3, 4]
    # 正常情况
    assert list(f([1, 4], [2, 3])) == [1, 2, 3, 4]


def test_percentage():
    # 分母为 0 的情况
    assert percentage(1, 0) == '0.00%'
    assert percentage(1, 0, with_format=False) == 0.0
    assert percentage(1, 0.0) == '0.00%'
    assert percentage(1, 0.0, with_format=False) == 0.0

    assert percentage(10, 100) == '10.00%'
    assert percentage(10, 100, with_format=False) == 10.0
    assert percentage(0.03, 4) == '0.75%'
    assert percentage(0.03, 4, with_format=False) == 0.75


def test_round_half_up():
    # 四舍五入, round 是奇进偶舍
    assert round_half_up(10499, -3) == 10000
    assert round_half_up(10500, -3) == 11000
    assert round(10500, -3) == 10000
    assert round_half_up(10501, -3) == 11000

    # 0.155 是无限小数, 0.154999...
    # 因此无论是奇进偶舍还是四舍五入都应该变为 0.16
    assert round(0.155, 2) == 0.15
    assert round_half_up(0.155, 2) == 0.16

    # 0.125 和 0.375 都是有限小数
    # 可以看出奇进偶舍和四舍五入的区别
    assert round(0.125, 2) == 0.12
    assert round(0.375, 2) == 0.38
    assert round_half_up(0.125, 2) == 0.13
    assert round_half_up(0.375, 2) == 0.38


class TestSeqGrouper:

    @pytest.mark.parametrize(('seq', 'filler'), (
        ('', '1'),
        (b'', b'1'),
        ([], 1),
        ((), 1),
    ))
    def test_empty(self, seq, filler):
        assert list(seq_grouper(seq, size=9)) == []
        assert list(seq_grouper(seq, size=9, filler=filler)) == []

    @pytest.mark.parametrize(('seq', 'filler'), (
        ('0123456789', '1'),
        (b'0123456789', b'1'),
    ))
    def test_text_type_not_empty(self, seq, filler):
        assert list(seq_grouper(seq, size=9)) == [seq[:9], seq[9:10]]
        assert list(seq_grouper(seq, size=10)) == [seq]
        assert list(seq_grouper(seq, size=11)) == [seq]
        assert list(seq_grouper(seq, size=9, filler=filler)) == \
            [seq[:9], seq[9:] + filler * 8]
        assert list(seq_grouper(seq, size=10, filler=filler)) == [seq]
        assert list(seq_grouper(seq, size=11, filler=filler)) == [seq + filler]

    @pytest.mark.parametrize(('seq', 'filler'), (
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], None),  # 检测了 `None` 用做填充值的情况.
        ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 1),
    ))
    def test_collection_type_not_empty(self, seq, filler):
        type_ = type(seq)
        assert list(seq_grouper(seq, size=9)) == [seq[:9], seq[9:10]]
        assert list(seq_grouper(seq, size=10)) == [seq]
        assert list(seq_grouper(seq, size=11)) == [seq]
        assert list(seq_grouper(seq, size=9, filler=filler)) == \
            [seq[:9], seq[9:] + type_(filler for _ in range(8))]
        assert list(seq_grouper(seq, size=10, filler=filler)) == [seq]
        assert list(seq_grouper(seq, size=11, filler=filler)) == [seq + type_([filler])]


def test_rm_around_space():
    textarea = """
    1

    2
    3

    """
    assert rm_around_space(textarea) == ['1', '2', '3']

    textarea = """
    1 a
    2\t\t b
    \t
    3      c
    """
    assert rm_around_space(textarea, keep_inline_space=False) == \
        [['1', 'a'], ['2', 'b'], ['3', 'c']]


def test_strip_control():
    assert strip_control('带\x00带\x1f我\x7f') == '带带我'
    assert strip_control('带\u0000带\u001f我\u007f') == '带带我'


class TestStripSeq:

    @pytest.mark.parametrize('seq', ('', b'', [], ()))
    def test_empty(self, seq):
        assert strip_seq(seq, size=9) == seq

    @pytest.mark.parametrize('item', ('1', b'1'))
    def test_text_type_not_empty(self, item):
        for i in range(4, 8):
            seq = item * i
            assert strip_seq(seq, size=4) == item * 4

    @pytest.mark.parametrize(('cls', 'item'), (
        (list, 1),
        (tuple, 2),
    ))
    def test_collection_type_not_empty(self, cls, item):
        for i in range(4, 8):
            seq = cls(item for _ in range(i))
            assert strip_seq(seq, size=4) == seq[:4]
