__all__ = (
    'AES',
)

import secrets
from typing import Tuple
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

backend = default_backend()


class CryptoException(Exception):
    """所有密码学工具库的异常基类."""
    pass


class SizeException(CryptoException):
    """密钥长度不符合要求."""
    pass


class AES:
    """AES 加密, 解密."""

    KEY_SIZES = {16, 24, 32}
    BLOCK_SIZE = 16

    def __init__(self, key: bytes, iv: bytes):
        if len(key) not in self.KEY_SIZES or len(iv) != self.BLOCK_SIZE:
            raise SizeException
        self.cipher = Cipher(
            algorithm=algorithms.AES(key),
            mode=modes.CBC(iv),
            backend=backend,
        )
        self.padding = padding.PKCS7(
            block_size=self.BLOCK_SIZE * 8,
        )

    def encrypt(self, msg: bytes) -> bytes:
        """加密."""
        encryptor = self.cipher.encryptor()
        padder = self.padding.padder()
        msg = padder.update(msg) + padder.finalize()
        return encryptor.update(msg) + encryptor.finalize()

    def decrypt(self, msg: bytes) -> bytes:
        """解密."""
        decryptor = self.cipher.decryptor()
        unpadder = self.padding.unpadder()
        plaintext = decryptor.update(msg) + decryptor.finalize()
        return unpadder.update(plaintext) + unpadder.finalize()

    @classmethod
    def generate_key(cls, key_size: int = 32) -> Tuple[bytes, bytes]:
        """生成 key 和 iv."""
        return secrets.token_bytes(key_size), secrets.token_bytes(cls.BLOCK_SIZE)
