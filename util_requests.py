__all__ = (
    'SessionWithUrlPrefix',
    'upload',
)

import os
from typing import IO, Optional, Union

from requests import Session, Response


class SessionWithUrlPrefix(Session):

    def __init__(self, url_prefix: Optional[str] = None):
        super().__init__()
        self.url_prefix = url_prefix

    def __repr__(self):
        return (
            f'<{self.__class__.__name__}'
            f' url_prefix={self.url_prefix!r}'
            f'>'
        )

    def request(self, method: str, url: str, *args, **kwargs) -> Response:
        url = self.url_prefix + url if self.url_prefix is not None else url
        return super().request(method, url, *args, **kwargs)


def upload(url: str, file: Union[str, IO],
           file_name: str = None) -> Response:
    """上传文件

    file: 可以是一个 str 代表文件路径, 也可以是一个类文件对象, 比如 io.StringIO.

    file_name: 上传的文件名, 如果不指定并且 ``file`` 类型是 str 则从 ``file`` 中提取,
               如果 ``file`` 类型不是 str, 则默认值为 data.csv
    """
    import requests

    if isinstance(file, str):
        file_name = os.path.split(file)[1] if file_name is None else file_name
        file = open(file)
    else:
        file_name = 'data.csv' if file_name is None else file_name

    r = requests.post(url=url, files={'file': (file_name, file)})
    return r
