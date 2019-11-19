__all__ = (
    'parse_phone',
)

from typing import Optional

import phonenumbers


def parse_phone(source: str) -> Optional[str]:
    try:
        pp = phonenumbers.parse(source, 'CN')
    except phonenumbers.NumberParseException:
        return None
    else:
        if phonenumbers.is_valid_number(pp):
            return str(pp.national_number)
        return None
