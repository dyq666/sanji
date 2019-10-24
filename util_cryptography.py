__all__ = (
    'AESCipher',
)

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

AES_BLOCK_BYTES_SIZE = algorithms.AES.block_size // 8


class AESCipher:

    def __init__(self, key: bytes, iv: bytes):
        """len(iv) == 16 == algorithms.AES.block_size / 8"""
        self.key = key
        self.iv = iv
        self.cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())

    def encrypt(self, content: bytes) -> bytes:
        """
        加密前将内容填充, 使其可以被 16 整除. 且填充字符是填充大小对应的 unicode.
        此外, 如果内容本身已可被 16 整除, 也需要补上 16 个填充字符.
        """
        filler_len = AES_BLOCK_BYTES_SIZE - (len(content) % AES_BLOCK_BYTES_SIZE)
        content += chr(filler_len).encode() * filler_len
        encryptor = self.cipher.encryptor()
        return encryptor.update(content) + encryptor.finalize()

    def decrypt(self, content: bytes) -> bytes:
        """
        加密后的最后一个字符一定是填充字符, 根据此填充字符可以删去填充字符序列.
        """
        decryptor = self.cipher.decryptor()
        msg = decryptor.update(content) + decryptor.finalize()
        filler_len = msg[-1]
        return msg[:-filler_len]
