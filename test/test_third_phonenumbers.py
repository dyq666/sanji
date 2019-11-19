from util import parse_phone


def test_parse_phone():
    tel = '17718809932'
    assert parse_phone(tel) == tel
    assert parse_phone(f'+86{tel}') == tel
    assert parse_phone(f'+87{tel}') is None
    assert parse_phone(tel[:10]) is None
