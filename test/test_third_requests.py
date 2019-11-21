import io
import os
import tempfile
from http import HTTPStatus

import requests

from util import OAuth2, SessionWithUrlPrefix, upload

HOST = 'http://localhost'
PORT = 5000


def test_o_auth2():
    s = requests.Session()

    r = s.get(f'{HOST}:{PORT}/o_auth2')
    assert r.status_code == HTTPStatus.UNAUTHORIZED

    s.auth = OAuth2(token='token')
    r = s.get(f'{HOST}:{PORT}/o_auth2')
    assert r.status_code == HTTPStatus.OK


def test_session_with_url_prefix():
    s = SessionWithUrlPrefix(f'{HOST}:{PORT}')

    r = s.get('/session_with_url_prefix')
    assert r.status_code == HTTPStatus.OK
    r = s.post('/session_with_url_prefix')
    assert r.status_code == HTTPStatus.OK
    r = s.delete('/session_with_url_prefix')
    assert r.status_code == HTTPStatus.OK
    r = s.put('/session_with_url_prefix')
    assert r.status_code == HTTPStatus.OK


class TestUpload:

    url = f'{HOST}:{PORT}/upload'

    def test_upload_io(self):
        f = io.StringIO()
        f.write('upload')
        f.seek(0)
        r = upload(self.url, file=f, file_name='test.txt')
        assert r.status_code == HTTPStatus.OK

    def test_upload_file(self):
        with tempfile.TemporaryDirectory() as dirname:
            filepath = os.path.join(dirname, 'test.txt')
            with open(filepath, 'w') as f:
                f.write('upload')
            r = upload(self.url, file=filepath)
            assert r.status_code == HTTPStatus.OK
            r = upload(self.url, file=filepath, file_name='test.txt')
            assert r.status_code == HTTPStatus.OK
