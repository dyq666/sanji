__all__ = (
    'AES',
    'AES_BLOCK_SIZE',
    'AES_CTR',
    'AES_KEY_SIZES',
    'Hybrid',
    'RSAPrivate',
    'RSAPublic',
)

import secrets
from typing import TYPE_CHECKING, Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asy_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

if TYPE_CHECKING:
    from cryptography.hazmat.backends.openssl.rsa import _RSAPrivateKey, _RSAPublicKey

AES_KEY_SIZES = {16, 24, 32}
AES_BLOCK_SIZE = 16

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

    def __init__(self, key: bytes, iv: bytes):
        if len(key) not in AES_KEY_SIZES or len(iv) != AES_BLOCK_SIZE:
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

    @staticmethod
    def generate_key(key_size: int = 32) -> bytes:
        if key_size not in AES_KEY_SIZES:
            raise ValueError
        return secrets.token_bytes(key_size)

    @staticmethod
    def generate_iv() -> bytes:
        return secrets.token_bytes(AES_BLOCK_SIZE)


class AES_CTR:
    """AES_CTR."""

    def __init__(self, key: bytes, nonce: bytes):
        if len(key) not in AES_KEY_SIZES or len(nonce) != AES_BLOCK_SIZE:
            raise ValueError
        self.cipher = Cipher(
            algorithm=algorithms.AES(key),
            mode=modes.CTR(nonce),
            backend=backend,
        )

    def encrypt(self, msg: bytes) -> bytes:
        encryptor = self.cipher.encryptor()
        return encryptor.update(msg) + encryptor.finalize()

    def decrypt(self, msg: bytes) -> bytes:
        decryptor = self.cipher.decryptor()
        return decryptor.update(msg) + decryptor.finalize()

    @staticmethod
    def generate_key(key_size: int = 32) -> bytes:
        if key_size not in AES_KEY_SIZES:
            raise ValueError
        return secrets.token_bytes(key_size)

    @staticmethod
    def generate_nonce() -> bytes:
        return secrets.token_bytes(AES_BLOCK_SIZE)


class Hybrid:
    """RSA + AES 加密消息, RSA 签名.

    通信双方各生成一对公钥, 并将公钥交给对方.
    发送时用自己的私钥签名, 另一方的公钥加密.
    接收时用自己的公钥验签, 另一方的私钥解密.
    """

    @staticmethod
    def encrypt(msg: bytes, private_sign_key: 'RSAPrivate',
                public_encrypt_key: 'RSAPublic') -> Tuple[bytes, bytes, bytes]:
        """加密 & 签名."""
        key = AES.generate_key()
        iv = AES.generate_iv()
        aes = AES(key, iv)

        signature = private_sign_key.sign(msg)
        ciphermsg = aes.encrypt(msg)
        session_key = public_encrypt_key.encrypt(key)
        return ciphermsg + iv, session_key, signature

    @staticmethod
    def decrypt(token: bytes, private_decrypt_key: 'RSAPrivate',
                public_verify_key: 'RSAPublic', session_key: bytes,
                signature: bytes) -> bytes:
        """解密 & 验签.

        如果验签失败会抛出 `cryptography.exceptions.InvalidSignature`.
        """
        msg, iv = token[:-16], token[-16:]
        key = private_decrypt_key.decrypt(session_key)
        aes = AES(key, iv)

        msg = aes.decrypt(msg)
        public_verify_key.verify(msg, signature)
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

    def verify(self, msg: bytes, signature: bytes):
        """验证签名.

        如果验证失败会抛出 `cryptography.exceptions.InvalidSignature`.
        """
        self.key.verify(
            signature=signature,
            data=msg,
            padding=rsa_sign_padding,
            algorithm=hashes.SHA256(),
        )

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
