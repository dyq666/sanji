__all__ = (
    'parse_phone',
)

from typing import Optional

import phonenumbers


def parse_phone(source: str) -> Optional[str]:
    """解析中国地区的手机号.

    将带 +86 前缀的手机号和正常的 11 位手机号都转换成 11 位手机号.
    """
    try:
        pp = phonenumbers.parse(source, 'CN')
    except phonenumbers.NumberParseException:
        return None
    else:
        if phonenumbers.is_valid_number(pp):
            return str(pp.national_number)
        return None
