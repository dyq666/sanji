import string
import pytest

from util import CaseInsensitiveDict, DictSerializer


class TestCaseInsensitiveDict:
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
        return CaseInsensitiveDict()

    def test_get_and_getitem(self, d):
        d['c'] = 2
        assert d.get('c') == 2
        assert d.get('C') == 2
        assert d.get('d') is None
        assert d.get('D', 1) == 1
        assert d['c'] == 2
        assert d['C'] == 2

    def test_setitem_and_len_and_items(self, d):
        d['c'] = 2
        assert dict(d.items()) == {'c': 2}
        assert len(d) == 1
        d['C'] = 2
        assert dict(d.items()) == {'c': 2}
        assert len(d) == 1

    def test_del_and_contains(self, d):
        d['c'] = 2
        assert 'C' in d
        del d['C']
        assert 'C' not in d
        assert None not in d

    def test_fromkeys_and_keys_and_values_and_iter(self):
        d = CaseInsensitiveDict.fromkeys(string.ascii_lowercase + string.ascii_uppercase, '1')
        assert ''.join(d.keys()) == string.ascii_lowercase
        assert ''.join(d) == string.ascii_lowercase
        assert ''.join(d.values()) == '1' * len(d)


class TestDictSerializer:

    @pytest.mark.parametrize('key', ('a:b', 'a|b', 'a$b', 'a:b|c$d'))
    @pytest.mark.parametrize('value', ('a', ['1', '2']))
    def test_single_encode_and_decode(self, key, value):
        data = {key: value}
        assert DictSerializer.decode(DictSerializer.encode(data)) == data

    def test_multi_encode_and_decode(self):
        data = {
            'a:b': 'a$b',
            'a|b': '',
            'a:b|c$d': ['A||%%A', '安$$安'],
        }
        assert DictSerializer.decode(DictSerializer.encode(data)) == data

    def test_empty(self):
        assert DictSerializer.encode({}) == ''
        assert DictSerializer.decode('') == {}
