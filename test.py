import os
from tempfile import TemporaryDirectory
from functools import partial

import pytest

from util import (
    Base64, CaseInsensitiveDict, Memoize, clean_textarea, fill_sequence,
    import_object, rm_control_chars, round_half_up, sequence_grouper, write_csv,
)
from util_cryptography import AESCipher, RSAPrivateKey, RSAPublicKey
from util_phonenumbers import parse_phone


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
        (Base64.b64encode, Base64.b64decode),
        (Base64.urlsafe_b64encode, Base64.urlsafe_b64decode),
    ))
    def test_encode_and_decode(self, with_equal, funcs):
        encode = partial(funcs[0], with_equal=with_equal)
        decode = partial(funcs[1], with_equal=with_equal)
        assert decode(encode(b'a')) == b'a'
        assert decode(encode(b'aa')) == b'aa'
        assert decode(encode(b'aaa')) == b'aaa'


def test_CaseInsensitiveDict():
    d = CaseInsensitiveDict()
    content_type = 'application/json'

    # __setitem__, __getitem__
    d['Content-Type'] = content_type
    assert d['content-type'] == content_type

    # get
    assert d.get('content-Type') == content_type
    assert d.get('dsa') is None
    assert d.get('dasda', 1) == 1

    # __delitem__, __contains__
    assert 'content-type' in d
    del d['ContenT-Type']
    assert 'content-type' not in d


def test_Memoize():
    class Foo:

        def __init__(self):
            self.id = 1

        @Memoize
        def foo(self):
            """I am foo"""
            return self.id + 100

    assert Foo.foo.__doc__ == 'I am foo'

    f = Foo()

    assert not hasattr(f, 'cache_key_foo')
    assert f.foo == f.__cache_foo == 101

    f.id = 2
    assert f.foo == f.__cache_foo == 101

    # 直接改缓存的属性
    f.__cache_foo = 2
    assert f.foo == f.__cache_foo == 2


def test_clean_textarea():
    textarea = """
    1

    2
    3

    """
    assert clean_textarea(textarea) == ['1', '2', '3']

    textarea = """
    1 a
    2\t\t b
    \t
    3      c
    """
    assert clean_textarea(textarea, keep_inline_space=False) == \
        [['1', 'a'], ['2', 'b'], ['3', 'c']]


class TestFillSequence:

    @pytest.mark.parametrize(('sequence', 'filler'), (
        ('', '1'),
        (b'', b'1'),
        ([], 1),
        ((), 1),
    ))
    def test_empty(self, sequence, filler):
        assert fill_sequence(sequence, size=9, filler=filler) == sequence

    @pytest.mark.parametrize(('item', 'filler'), (
        ('1', '='),
        (b'1', b'='),
    ))
    def test_text_type_not_empty(self, item, filler):
        for i in range(1, 5):
            sequence = item * i
            fillers = filler * (4 - i)
            assert fill_sequence(sequence, 4, filler) == sequence + fillers

    @pytest.mark.parametrize(('cls', 'item', 'filler'), (
        (list, 1, '='),
        (tuple, 2, '='),
    ))
    def test_collection_type_not_empty(self, cls, item, filler):
        for i in range(1, 5):
            sequence = cls(item for _ in range(i))
            fillers = cls(filler for _ in range(4 - i))
            assert fill_sequence(sequence, 4, filler) == sequence + fillers


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


def test_rm_control_chars():
    assert rm_control_chars('带\x00带\x1f我\x7f') == '带带我'
    assert rm_control_chars('带\u0000带\u001f我\u007f') == '带带我'


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


class TestSequenceGrouper:

    @pytest.mark.parametrize(('sequence', 'filler'), (
        ('', '1'),
        (b'', b'1'),
        ([], 1),
        ((), 1),
    ))
    def test_empty(self, sequence, filler):
        assert list(sequence_grouper(sequence, size=9)) == []
        assert list(sequence_grouper(sequence, size=9, filler=filler)) == []

    @pytest.mark.parametrize(('sequence', 'filler'), (
        ('0123456789', '1'),
        (b'0123456789', b'1'),
    ))
    def test_text_type_not_empty(self, sequence, filler):
        assert list(sequence_grouper(sequence, size=9)) == [sequence[:9], sequence[9:10]]
        assert list(sequence_grouper(sequence, size=10)) == [sequence]
        assert list(sequence_grouper(sequence, size=11)) == [sequence]
        assert list(sequence_grouper(sequence, size=9, filler=filler)) == \
            [sequence[:9], sequence[9:] + filler * 8]
        assert list(sequence_grouper(sequence, size=10, filler=filler)) == [sequence]
        assert list(sequence_grouper(sequence, size=11, filler=filler)) == [sequence + filler]

    @pytest.mark.parametrize(('sequence', 'filler'), (
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 1),
        ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 1),
    ))
    def test_collection_type_not_empty(self, sequence, filler):
        type_ = type(sequence)
        assert list(sequence_grouper(sequence, size=9)) == [sequence[:9], sequence[9:10]]
        assert list(sequence_grouper(sequence, size=10)) == [sequence]
        assert list(sequence_grouper(sequence, size=11)) == [sequence]
        assert list(sequence_grouper(sequence, size=9, filler=filler)) == \
            [sequence[:9], sequence[9:] + type_(filler for _ in range(8))]
        assert list(sequence_grouper(sequence, size=10, filler=filler)) == \
            [sequence]
        assert list(sequence_grouper(sequence, size=11, filler=filler)) == \
            [sequence + type_([filler])]


class TestWriteCSV:

    header = ('name', 'sex')
    rows = (('father', 'male'), ('mother', 'female'))
    content = 'name,sex\nfather,male\nmother,female\n'

    def test_expected_exceptions(self):
        with pytest.raises(ValueError):
            write_csv((), ())
        with pytest.raises(TypeError):
            write_csv(('1',), ({1}))

    def test_row_item_type(self):
        rows_fixtures = (
            self.rows,
            tuple(list(row) for row in self.rows),
            tuple({header: datum for header, datum in zip(self.header, row)}
                  for row in self.rows),
        )
        for rows in rows_fixtures:
            file = write_csv(self.header, rows)
            assert file.getvalue().replace('\r\n', '\n') == self.content

    def test_out_path_arg(self):
        header = self.header
        rows = self.rows
        csv_content = self.content

        file = write_csv(header, rows)
        assert file.getvalue().replace('\r\n', '\n') == csv_content

        with TemporaryDirectory() as dirname:
            file_path = os.path.join(dirname, 'data.csv')
            write_csv(header, rows, file_path)

            with open(file_path) as f:
                assert f.read() == csv_content


"""test util_cryptography"""


class TestAESCiper:

    key = os.urandom(16)
    iv = os.urandom(16)
    ciper = AESCipher(key, iv)

    def test_filler(self):
        """确保填充字符等于需要填充的个数"""
        for i in range(1, 17):
            content = b'-' * i
            encrypted_content = self.ciper.encrypt(content)
            decryptor = self.ciper.cipher.decryptor()
            decrypted_content = decryptor.update(encrypted_content) + decryptor.finalize()
            assert decrypted_content[-1] == 16 - (i % 16)

    def test_encrypt_and_decrypt(self):
        for i in range(1, 17):
            content = b'-' * i
            encrypted_content = self.ciper.encrypt(content)
            assert content == self.ciper.decrypt(encrypted_content)


class TestRsa:

    def test_load_private_key(self):
        """load 后的 private key 应该生成一样的 public key"""
        private_key = RSAPrivateKey.generate()
        private_key2 = RSAPrivateKey.load(private_key.format_private_key())
        assert private_key.format_public_key() == private_key2.format_public_key()

    def test_encrpty_and_decrpty(self):
        content = '带带我666'.encode()
        private_key = RSAPrivateKey.generate()
        public_key = RSAPublicKey.load(private_key.format_public_key())
        assert private_key.decrypt(public_key.encrypt(content)) == content


"""test util_phonenumbers"""


def test_parse_phone():
    tel = '17718809932'
    assert parse_phone(tel) == tel
    assert parse_phone(f'+86{tel}') == '17718809932'
    assert parse_phone(f'+87{tel}') is None
    assert parse_phone(tel[:10]) is None
