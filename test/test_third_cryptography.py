"""
由于 RSA 生成速度比较慢, 因此提前设置好了两组 key, 第一组没密码, 第二组密码为 b'1'.
"""

import pytest
from cryptography.exceptions import InvalidSignature

from util import (
    AES, AES_BLOCK_SIZE, AES_CTR, AES_KEY_SIZES, Hybrid,
    RSAPrivate, RSAPublic,
)


@pytest.fixture
def private_pem():
    return (
        b'-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEF'
        b'AASCBKcwggSjAgEAAoIBAQDh4rAaLoYAdNW6\nR+uXIE9zsttUkAte4LdU'
        b'e/t6VZMEbvCC8H6YXsLSCEhBQsMSEAoeMBAbLo+trDOU\npO8FlgDrJK3Z'
        b'nabN4Uves3m1YFJm/12fiHz11olRvFsCGV/Yxpl/kbZhXApN9G8W\nswry'
        b'6bQsx2V5bnTuqxt2J29YzSbwOzAyHSe+Jci7dN2xtTCekA1GgcCQRspZxmR'
        b'g\nRi+pKMXue0X4PIsRGU8wjl0vPRTYcQVy0rBk/IQADgWh/PRPq1c5gKSQ'
        b'ounrjGVK\nfpSrtqyGw7seISxk3om/yIQ+gE0Gjwz0i2YejKiY5QjMrhWoO'
        b'BKzw0/Cv2hC48J0\neEix3raRAgMBAAECggEAUBOtvEpb5NOGZRhT82pX4D'
        b's6t9qsvUDKnR+qwe6ORNcT\nWkfpiRim1hBrlP8W6lNXUuZU/13dP4M5ceua'
        b'dI992d5R50CVPo0s+VEEx4DTFYJX\n7VNUgU5BtgEg/jiCmvWkuu2sCw229X'
        b'W+3/wu2HhzECDL32WB/I4aGSPXvFJWCHk4\nXCrlJ239R5ORCiBIfartSRQR'
        b'ChD1Hpwux4Nht0MtWO4vS6Uyxl7kSRDBbzWBynVT\nLTsvFy0w3U3F4CPUaIU'
        b'mGSeo/ckjSjrZnjQ9mUXaVkEgcldDPBtcT+OWDEa3OG0h\nw7vB8R0RlAM4EM'
        b'r/MH+KweHx+aBPt4ybx1b4jjj28QKBgQD9a+z+7ohoAnv4Di/C\nfGnu+tJd'
        b'lUkJvGT0gO5vA7WcIJuTfRlKhOa9/brbKTrPJUvkxunCyIWOUTlFz8o8\n6X'
        b'kyVNEt9SjSEODy77t8lcsdNAbR3FYSslRGIUveRJSuT76g6WhVNLX7A6ga1'
        b'qTu\neZiTMakX2Nn6c6ZUKUeVLgTUlQKBgQDkLwpROXLnTNA1c42C3w/RGQn'
        b'tSX0/vlh2\noVw2biXLI/Jnlok6AdlaByAJ/vfvxoaddBLXFbOYg3Fm2FxiLQ'
        b'Yu6sU8ICcqL3gL\nrkDPUqD6U1814z6BSs1uIHzp2ofIui6ZA0OH83gKeHss'
        b'hpdAdv9es1Z1tjyjmAg6\neQrR2QJ/DQKBgQC+mM9UJP6+iy/FrpXJBl19+X'
        b'MCI2cdRW4AXn/1SqrqU7Pux2Wg\nIDiSqCRC9M1gQkLEO75QWxPnp7sVgGQw'
        b'T8BxVE1G7V3YMA2faSJvXxG2UwzWBYtO\n4IR1glFXR+ky+JL83s8zVkOQGH'
        b'30QX8mRJm2CuGMJ/I5ZYWxQqKt1kCXyQKBgC0h\naKb798/rj1qjCiASQiyX'
        b'CTGXUWBkI1cDPxu82Vi+OVlnmqiQaQ63TgzsEtmnqERI\nCtnjfuvxQ2KV9'
        b'F+ujASHho8HxPdBADs/Ma5Pp2sbRj+APIKR6uOXJV2TTTvUJxc4\nYAjpjJp'
        b'1jdcWn5+uaX+vdLA/ZOruTOJTwmISy72ZAoGAL1xaSPA9D/LJ/yMoXi+a\ny'
        b'a3vmg+HRgara2vKqyvBGj9I5g+WdmWwF2HNAl/6zO+I8MB8tPmQalDbOUA0'
        b'1dPm\nJXHBq4OM8Ufh/8VHPg10IltcQjzIDG9xIGjO2nRJ+gHIKjKhnARSw'
        b'tmsTVn6iXZt\nOLU4umXwyDW1G1dc4blHvXw=\n-----END PRIVATE KEY-----\n'
    )


@pytest.fixture
def public_pem():
    return (
        b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A'
        b'MIIBCgKCAQEA4eKwGi6GAHTVukfrlyBP\nc7LbVJALXuC3VHv7elWTBG7wgv'
        b'B+mF7C0ghIQULDEhAKHjAQGy6PrawzlKTvBZYA\n6ySt2Z2mzeFL3rN5tWBS'
        b'Zv9dn4h89daJUbxbAhlf2MaZf5G2YVwKTfRvFrMK8um0\nLMdleW507qsbdi'
        b'dvWM0m8DswMh0nviXIu3TdsbUwnpANRoHAkEbKWcZkYEYvqSjF\n7ntF+DyL'
        b'ERlPMI5dLz0U2HEFctKwZPyEAA4Fofz0T6tXOYCkkKLp64xlSn6Uq7as\nhs'
        b'O7HiEsZN6Jv8iEPoBNBo8M9ItmHoyomOUIzK4VqDgSs8NPwr9oQuPCdHhIsd'
        b'62\nkQIDAQAB\n-----END PUBLIC KEY-----\n'
    )


@pytest.fixture
def private_pem_with_key():
    return (
        b'-----BEGIN ENCRYPTED PRIVATE KEY-----\nMIIFLTBXBgkqhkiG9w0BBQ'
        b'0wSjApBgkqhkiG9w0BBQwwHAQIpKdHqcubDrkCAggA\nMAwGCCqGSIb3DQIJB'
        b'QAwHQYJYIZIAWUDBAEqBBAbF+ZK2sM5pS0ztqJCO6KQBIIE\n0OJsODWJhUxM'
        b'OJJoNNfI8dGr04tJRggh1Yfv9Y9/oNR36UJB4NpHdDxYAIRlpRKK\nQpxARNQ'
        b'+U+d5EuiNV7sbxBdgWg/jH2W2FuOF1wRtVaYuFbscO4KRn0y01tXKfizR\npe'
        b'+Lu0RmXwOvkFncYYZ+h4fODzMOYB5VJ1C1h1Ir7ssXcX+f6JTgK4CDpxMWJnf'
        b'H\nrEK7EXktgCoBshqZtIwNVnoXiPyfuPpGy3e+Odo05ciraUfZj9lq4NnQH7C'
        b'0cBqT\niKbossRpLe8dXjl5mUBrtm6BPPJnX/nDzHGxGwUi8oFmG2Go2SSJH/R'
        b'DG4RAk7bk\nDKOYTmD1eS7USlWH55xu58YCA/0a5GrtjvW56MKx6iS5bul0JP'
        b'Bc3n80k9xkGJZ5\neyyIT0GhEm/aHu3vCjrLiPkru8SlPmTA9RPzQlvSq9RBt'
        b'OdpXHvXzB3iXS1Z5xqz\n8jCEzP2vwT9NBMjBcFfJyAjIOfImsOLHcHrZEk+E'
        b'12+wEBLmf3OcHqrQZ6IQgOTq\nGOGp3UGKq9RYC1daoHQPWUPRLtJ4aUZAUMU'
        b'XKg5gclrkXYtSMNmARmDVV09WRKMC\nRWMZNglbbJcjqPaOcqB80rkH6frwx'
        b'YDudOJjew+VSzl3w9kT644fH+k9x4KL51Nu\nQJsBMaLDCLQ4B29ndpdZ4Nyk'
        b'Cf/HEsIOWRO/t9f9lg3r3MouHr3Reb0ZgadRuWgM\nkj6wGj5afTTqGx9iGiz'
        b'exGBhzzWRBufVjhkKjARz39ymXh/A81cvcUaMlbKhpw03\nO8upunjF11exm'
        b'K1pqZpRuFB8qKW8fyco01ctN4uHNNQOoG+bBa5Y+xyhHgMaVwgP\nuI1sOwZ7'
        b'5kEZh/7g747mL36dKhHKH7S7MWAN6QEZngLV3XmEqOdLfK+7pucCqrrB\npK6'
        b'6ZNrjaX7OwmJ+ade4Xe6xOttrETP386He3aRZogV7YTKX7ExI8vZNAuSai4Gs'
        b'\nRdywynYFmiHUg/+cZgKNDUQyFsPeFkVssxawpCHwlPi890tjXLptww5XrNV'
        b'5krf9\nuyMUbMU8JePqS7n6PlN4DaN1ZM808q6dOlUB5PYf88PfVC3BwHL7VX'
        b'eq9M8LquTo\n9iIOI1OkohbvEjn4Y1TR859FRXW8hZGTxtYmPiwKOPSrRhKv'
        b'a/c4X93CKAuEJSYp\nlmqvolneeszlp5umV6KWqE2LGkhBkAXUAc63ZRWX7Pas'
        b'6g2kpNey/+2qOgGXC0Ks\nSYrb6RrV4WLJSf+M1xR80bAT+DLkxQEiJEGZs7M'
        b'2T1x1oMRpx+7W6xukbfUtQB6l\nHVjgnE3HDyldnfjckXecSElxRA0TAaOnVQ'
        b'2TUSfd6PzjBNC1V4/8P8qwndnmQrpo\n3wTmkcBkTPP+0eHqRYQsDpuzIJUgs'
        b'WnfHuACGstlRl1A4eVNI1EDQKCouvXZ4OM9\nOzpwE+k6yyAaSRJupbZkz1U7'
        b'H0imd29yHYSxo2zdPiG23hFFsbdBuroKVfqIdbcR\npkqk53s1igqXe0L60G'
        b'MJfpwYHeEL5vmgx/I9wJmIXwqclXauWRzWQDyBTmSslEbt\n1xPsPPKavQtn'
        b'o9tUYun2gGalyGA2b/W6uf3vFXGQEOOLI+zF7YvuVFf1j8Z67HFW\nEfAvol'
        b'P8f9bAXRmAsklgJzvnME6FGFAGyd4AYIb4Lt4h\n-----END ENCRYPTED '
        b'PRIVATE KEY-----\n'
    )


@pytest.fixture
def public_pem_with_key():
    return (
        b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC'
        b'AQEA0aGWQ+DdGFYaMfUJQs4s\n0viy9vVH7R+u8IDNAEu0GHTBdvTHmmAf3cozPTIcb'
        b'H1+FaO/51z/a0T9y3ejS91p\nWJYtuGnx3/w0hQ4v/ivbufAcJQsPJYsYA2JuJU5s6'
        b'/iVK1UcaPdtvfEomRLDSxS4\nNnELK8pko8iaQKR9HzAz/EmLZME3Mf43cBQFW2/2V2'
        b'imaJLfqmXrbbR0mGhe5k8Q\nHXPgM+VPtv/AtdqS75+sj/jI9hMHgvKKuAJ7hH2GTpo'
        b'xT2n+TR5IQ+ymAFP6PKc2\nZheWWB1aYeOvOWyuUwiJUAEtBjk3jFXjoTjzL7NFtH'
        b'ApnhV77LuLsfI7kubvKRXr\nWwIDAQAB\n-----END PUBLIC KEY-----\n'
    )


@pytest.mark.parametrize('key_size', AES_KEY_SIZES)
@pytest.mark.parametrize('msg', (b'1', b'1' * AES_BLOCK_SIZE))
def test_aes(key_size, msg):
    key = AES.generate_key(key_size=key_size)
    iv = AES.generate_iv()
    aes = AES(key, iv)
    assert aes.decrypt(aes.encrypt(msg)) == msg


@pytest.mark.parametrize('key_size', AES_KEY_SIZES)
@pytest.mark.parametrize('msg', (b'1', b'1' * AES_BLOCK_SIZE))
def test_aes(key_size, msg):
    key = AES_CTR.generate_key(key_size=key_size)
    nonce = AES_CTR.generate_nonce()
    aes_ctr = AES_CTR(key, nonce)
    assert aes_ctr.decrypt(aes_ctr.encrypt(msg)) == msg


@pytest.mark.parametrize('msg', (b'1', b'1' * AES_BLOCK_SIZE))
def test_hybrid(msg, private_pem, public_pem,
                private_pem_with_key, public_pem_with_key):
    alice_private_key = RSAPrivate.load_pem(private_pem)
    alice_public_key = RSAPublic.load_pem(public_pem)
    bob_private_key = RSAPrivate.load_pem(private_pem_with_key, password=b'1')
    bob_public_key = RSAPublic.load_pem(public_pem_with_key)

    # alice 向 bob 发送消息
    token, session_key, signature = Hybrid.encrypt(
        msg,
        private_sign_key=alice_private_key,
        public_encrypt_key=bob_public_key,
    )
    assert msg == Hybrid.decrypt(
        token,
        public_verify_key=alice_public_key,
        private_decrypt_key=bob_private_key,
        session_key=session_key,
        signature=signature,
    )

    # bob 向 alice 发送消息
    token, session_key, signature = Hybrid.encrypt(
        msg,
        private_sign_key=bob_private_key,
        public_encrypt_key=alice_public_key,
    )
    assert msg == Hybrid.decrypt(
        token,
        public_verify_key=bob_public_key,
        private_decrypt_key=alice_private_key,
        session_key=session_key,
        signature=signature,
    )


class TestRSAPrivate:

    @pytest.mark.skipif(True, reason='生成 rsa-key 的操作比较耗时, 测试时要手动开启.')
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
    def test_encrypt_and_sign(self, password, private_pem, public_pem,
                              private_pem_with_key, public_pem_with_key):
        if password is not None:
            private_pem = private_pem_with_key
            public_pem = public_pem_with_key

        private = RSAPrivate.load_pem(private_pem, password)
        public = RSAPublic.load_pem(public_pem)
        public_2 = RSAPublic.load_ssh(public.format_ssh())

        msgs = (b'1', '谢谢'.encode())
        for msg in msgs:
            assert private.decrypt(public.encrypt(msg)) == msg
            assert private.decrypt(public_2.encrypt(msg)) == msg
            assert public.verify(msg, private.sign(msg)) is None
            with pytest.raises(InvalidSignature):
                public.verify(msg + b'1', private.sign(msg))
            assert public_2.verify(msg, private.sign(msg)) is None
            with pytest.raises(InvalidSignature):
                public_2.verify(msg + b'1', private.sign(msg))
