import pytest

from util import AES, RSAPrivate


@pytest.mark.parametrize('key_size', AES.KEY_SIZES)
@pytest.mark.parametrize('msg', (b'1', b'1' * AES.BLOCK_SIZE))
def test_aes(key_size, msg):
    key, iv = AES.generate_key(key_size=key_size)
    aes = AES(key, iv)
    ciphertext = aes.encrypt(msg)
    assert msg == aes.decrypt(ciphertext)


class TestRSAPrivate:

    @pytest.mark.parametrize('password', (None, b'1'))
    def test_generate_key(self, password):
        private, public = RSAPrivate.generate_key(password)

        private_group = [item for item in private.split(b'\n') if item]
        assert private_group[0] == b'-----BEGIN RSA PRIVATE KEY-----'
        assert private_group[-1] == b'-----END RSA PRIVATE KEY-----'
        public_group = [item for item in public.split(b'\n') if item]
        assert public_group[0] == b'-----BEGIN PUBLIC KEY-----'
        assert public_group[-1] == b'-----END PUBLIC KEY-----'

        assert RSAPrivate.load(private, password)._format_public_key() == public
