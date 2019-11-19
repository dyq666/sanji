import os
from util import AESCipher, RSAPrivateKey, RSAPublicKey


class TestAESCiper:

    key = os.urandom(16)
    iv = os.urandom(16)
    ciper = AESCipher(key, iv)

    def test_filler(self):
        """确保填充字符等于需要填充的个数"""
        for i in range(1, 17):
            content = b'-' * i
            encrypted_content = self.ciper.encrypt(content)
            decryptor = self.ciper.cipher.decryptor()
            decrypted_content = decryptor.update(encrypted_content) + decryptor.finalize()
            assert decrypted_content[-1] == 16 - (i % 16)

    def test_encrypt_and_decrypt(self):
        for i in range(1, 17):
            content = b'-' * i
            encrypted_content = self.ciper.encrypt(content)
            assert content == self.ciper.decrypt(encrypted_content)


class TestRsa:

    def test_load_private_key(self):
        """load 后的 private key 应该生成一样的 public key"""
        private_key = RSAPrivateKey.generate()
        private_key2 = RSAPrivateKey.load(private_key.format_private_key())
        assert private_key.format_public_key() == private_key2.format_public_key()

    def test_encrpty_and_decrpty(self):
        content = '带带我666'.encode()
        private_key = RSAPrivateKey.generate()
        public_key = RSAPublicKey.load(private_key.format_public_key())
        assert private_key.decrypt(public_key.encrypt(content)) == content
