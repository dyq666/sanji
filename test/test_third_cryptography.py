import pytest

from util import AES


@pytest.mark.parametrize('key_size', AES.KEY_SIZES)
@pytest.mark.parametrize('msg', (b'1', b'1' * AES.BLOCK_SIZE))
def test_aes(key_size, msg):
    key, iv = AES.generate_key(key_size=key_size)
    aes = AES(key, iv)
    ciphertext = aes.encrypt(msg)
    assert msg == aes.decrypt(ciphertext)
