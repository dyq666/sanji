import string
from collections import namedtuple

import pytest

from util import (
    AttrGettingProxy, CaseInsensitiveDict, DefaultDict,
    DictSerializer, MockName, base_conversion
)


def test_attr_getting_proxy():
    # 被包裹一层的 tuple 只能获取属性.
    a = (1, 2)
    obj = AttrGettingProxy(a)
    with pytest.raises(TypeError):
        len(obj)
    assert obj.index(1) == 0

    # 被包裹一层的 list 只能获取属性.
    b = [1, 2]
    obj = AttrGettingProxy(b)
    with pytest.raises(TypeError):
        obj[1]
    assert obj.index(1) == 0


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
        # get 的 default 参数会失效, 因为在 DefaultDict 中所有 key 都是存在的.
        assert d.get('d', 'error') == 'default'

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


def test_mock_name():
    People = namedtuple('People', 'name age')
    people = People('bob', 18)
    mock = MockName(people)

    assert mock.name == 'mock'
    assert mock.age == 18


def test_base_conversion():
    with pytest.raises(ValueError):
        base_conversion(-2)
    with pytest.raises(ValueError):
        base_conversion(1, base=0)
    with pytest.raises(ValueError):
        base_conversion(1, base=11)

    assert ''.join(str(i) for i in reversed(base_conversion(0))) == '0'
    assert ''.join(str(i) for i in reversed(base_conversion(0, base=3))) == '0'
    assert ''.join(str(i) for i in reversed(base_conversion(0, base=10))) == '0'

    assert ''.join(str(i) for i in reversed(base_conversion(10))) == '1010'
    assert ''.join(str(i) for i in reversed(base_conversion(10, base=3))) == '101'
    assert ''.join(str(i) for i in reversed(base_conversion(10, base=10))) == '10'
