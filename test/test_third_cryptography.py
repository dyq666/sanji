import pytest

from util import AES, RSAPrivate, RSAPublic


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
        private_pem, public_pem = RSAPrivate.generate_key(password)

        private_group = [item for item in private_pem.split(b'\n') if item]
        if password is None:
            assert private_group[0] == b'-----BEGIN PRIVATE KEY-----'
            assert private_group[-1] == b'-----END PRIVATE KEY-----'
        else:
            assert private_group[0] == b'-----BEGIN ENCRYPTED PRIVATE KEY-----'
            assert private_group[-1] == b'-----END ENCRYPTED PRIVATE KEY-----'
        public_group = [item for item in public_pem.split(b'\n') if item]
        assert public_group[0] == b'-----BEGIN PUBLIC KEY-----'
        assert public_group[-1] == b'-----END PUBLIC KEY-----'

    @pytest.mark.parametrize('password', (None, b'1'))
    def test_encrypt_and_decrypt(self, password):
        private_pem, public_pem = RSAPrivate.generate_key(password)
        private = RSAPrivate.load_pem(private_pem, password)
        public = RSAPublic.load_pem(public_pem)
        public_2 = RSAPublic.load_ssh(public.format_ssh())

        msgs = (b'1', '谢谢'.encode())
        for msg in msgs:
            assert private.decrypt(public.encrypt(msg)) == msg
            assert private.decrypt(public_2.encrypt(msg)) == msg

    @pytest.mark.parametrize('password', (None, b'1'))
    def test_encrypt_and_decrypt(self, password):
        private_pem, public_pem = RSAPrivate.generate_key(password)
        private = RSAPrivate.load_pem(private_pem, password)
        public = RSAPublic.load_pem(public_pem)

        msgs = (b'1', '谢谢'.encode())
        for msg in msgs:
            assert public.verify(private.sign(msg), msg)
            assert not public.verify(private.sign(msg), msg + b'1')
