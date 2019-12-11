import enum
import os
import tempfile
from functools import partial

import pytest

from util import (
    CSV, Base64, Binary, BitField, camel2snake, chinese_num, fill_seq,
    import_object, indent_data, round_half_up, seq_grouper, strip_blank,
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


class TestFillSeq:

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
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 1),
        ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 1),
    ))
    def test_collection_type_not_empty(self, seq, filler):
        type_ = type(seq)
        assert list(seq_grouper(seq, size=9)) == [seq[:9], seq[9:10]]
        assert list(seq_grouper(seq, size=10)) == [seq]
        assert list(seq_grouper(seq, size=11)) == [seq]
        assert list(seq_grouper(seq, size=9, filler=filler)) == \
            [seq[:9], seq[9:] + type_(filler for _ in range(8))]
        assert list(seq_grouper(seq, size=10, filler=filler)) == \
            [seq]
        assert list(seq_grouper(seq, size=11, filler=filler)) == \
            [seq + type_([filler])]


def test_strip_blank():
    textarea = """
    1

    2
    3

    """
    assert strip_blank(textarea) == ['1', '2', '3']

    textarea = """
    1 a
    2\t\t b
    \t
    3      c
    """
    assert strip_blank(textarea, keep_inline_space=False) == \
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
