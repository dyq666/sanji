__all__ = (
    'AES',
    'HybridEncryption',
    'RSAPrivate',
    'RSAPublic',
)

import secrets
from typing import TYPE_CHECKING, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asy_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

if TYPE_CHECKING:
    from cryptography.hazmat.backends.openssl.rsa import _RSAPrivateKey, _RSAPublicKey

backend = default_backend()
rsa_sign_padding = asy_padding.PSS(
    mgf=asy_padding.MGF1(hashes.SHA256()),
    salt_length=asy_padding.PSS.MAX_LENGTH,
)
rsa_padding = asy_padding.OAEP(
    mgf=asy_padding.MGF1(hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)
aes_padding = padding.PKCS7(algorithms.AES.block_size)


class AES:
    """AES_256_CBC, 填充方式: PKCS7."""

    KEY_SIZES = {16, 24, 32}
    BLOCK_SIZE = 16

    def __init__(self, key: bytes, iv: bytes):
        if len(key) not in self.KEY_SIZES or len(iv) != self.BLOCK_SIZE:
            raise ValueError
        self.cipher = Cipher(
            algorithm=algorithms.AES(key),
            mode=modes.CBC(iv),
            backend=backend,
        )

    def encrypt(self, msg: bytes) -> bytes:
        """加密."""
        encryptor = self.cipher.encryptor()
        padder = aes_padding.padder()
        msg = padder.update(msg) + padder.finalize()
        return encryptor.update(msg) + encryptor.finalize()

    def decrypt(self, msg: bytes) -> bytes:
        """解密."""
        decryptor = self.cipher.decryptor()
        unpadder = aes_padding.unpadder()
        msg = decryptor.update(msg) + decryptor.finalize()
        return unpadder.update(msg) + unpadder.finalize()

    @classmethod
    def generate_key(cls, key_size: int = 32) -> Tuple[bytes, bytes]:
        """生成 key 和 iv."""
        if key_size not in cls.KEY_SIZES:
            raise ValueError
        return secrets.token_bytes(key_size), secrets.token_bytes(cls.BLOCK_SIZE)


class HybridEncryption:
    """RSA + AES 混合加密."""

    @staticmethod
    def encrypt(msg: bytes, public_key: 'RSAPublic') -> Tuple[bytes, bytes]:
        key, iv = AES.generate_key()
        aes = AES(key, iv)
        ciphermsg = aes.encrypt(msg)
        cipherkey = public_key.encrypt(key)
        return ciphermsg + iv, cipherkey

    @staticmethod
    def decrypt(token: bytes, private_key: 'RSAPrivate', key: bytes) -> bytes:
        msg, iv = token[:-16], token[-16:]
        key = private_key.decrypt(key)
        aes = AES(key, iv)
        msg = aes.decrypt(msg)
        return msg


class RSAPrivate:
    """RSA 私钥相关的操作."""

    def __init__(self, key: '_RSAPrivateKey'):
        self.key = key

    def decrypt(self, msg: bytes) -> bytes:
        """解密."""
        return self.key.decrypt(
            ciphertext=msg,
            padding=rsa_padding,
        )

    def sign(self, msg: bytes) -> bytes:
        """签名."""
        return self.key.sign(
            data=msg,
            padding=rsa_sign_padding,
            algorithm=hashes.SHA256(),
        )

    def format_pem(self, password: Optional[bytes] = None) -> bytes:
        """生成 PEM 格式的私钥."""
        if password is None:
            algorithm = serialization.NoEncryption()
        else:
            algorithm = serialization.BestAvailableEncryption(password)

        return self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=algorithm,
        )

    @classmethod
    def generate_key(cls, password: Optional[bytes] = None
                     ) -> Tuple[bytes, bytes]:
        """生成 PEM 格式的私钥和公钥."""
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=backend,
        )
        private_key = cls(key)
        public_key = RSAPublic(key.public_key())
        return private_key.format_pem(password), public_key.format_pem()

    @classmethod
    def load_pem(cls, msg: bytes, password: Optional[bytes] = None
                 ) -> 'RSAPrivate':
        """加载 PEM 格式的私钥."""
        key = serialization.load_pem_private_key(
            data=msg,
            password=password,
            backend=backend,
        )
        return cls(key)


class RSAPublic:
    """RSA 公钥相关的操作."""

    def __init__(self, key: '_RSAPublicKey'):
        self.key = key

    def encrypt(self, msg: bytes) -> bytes:
        """加密."""
        return self.key.encrypt(
            plaintext=msg,
            padding=rsa_padding,
        )

    def verify(self, signature: bytes, msg: bytes) -> bool:
        """验证签名."""
        try:
            self.key.verify(
                signature=signature,
                data=msg,
                padding=rsa_sign_padding,
                algorithm=hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False

    def format_pem(self) -> bytes:
        """生成 PEM 格式的公钥."""
        return self.key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def format_ssh(self) -> bytes:
        """生成 SSH 格式的公钥."""
        return self.key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

    @classmethod
    def load_pem(cls, msg: bytes) -> 'RSAPublic':
        """加载 PEM 格式的公钥."""
        key = serialization.load_pem_public_key(
            data=msg,
            backend=backend,
        )
        return cls(key)

    @classmethod
    def load_ssh(cls, msg: bytes) -> 'RSAPublic':
        """加载 SSH 格式的公钥."""
        key = serialization.load_ssh_public_key(
            data=msg,
            backend=backend,
        )
        return cls(key)
