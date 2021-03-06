import os
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.keywrap import (
    aes_key_wrap,
    aes_key_unwrap
)
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import GCM
from authlib.common.encoding import (
    to_bytes, to_native,
    urlsafe_b64decode,
    urlsafe_b64encode
)
from authlib.jose.rfc7516 import JWEAlgorithm
from ._keys_cryptography import RSAKey, ECKey
from ..oct_key import OctKey


class RSAAlgorithm(JWEAlgorithm):
    #: A key of size 2048 bits or larger MUST be used with these algorithms
    #: RSA1_5, RSA-OAEP, RSA-OAEP-256
    key_size = 2048

    def __init__(self, name, description, pad_fn):
        self.name = name
        self.description = description
        self.padding = pad_fn

    def prepare_key(self, raw_data):
        return RSAKey.import_key(raw_data)

    def wrap(self, cek, headers, key):
        op_key = key.get_op_key('wrapKey')
        if op_key.key_size < self.key_size:
            raise ValueError('A key of size 2048 bits or larger MUST be used')
        ek = op_key.encrypt(cek, self.padding)
        return ek

    def unwrap(self, ek, headers, key):
        # it will raise ValueError if failed
        op_key = key.get_op_key('unwrapKey')
        return op_key.decrypt(ek, self.padding)


class AESAlgorithm(JWEAlgorithm):
    def __init__(self, key_size):
        self.name = 'A{}KW'.format(key_size)
        self.description = 'AES Key Wrap using {}-bit key'.format(key_size)
        self.key_size = key_size

    def prepare_key(self, raw_data):
        return OctKey.import_key(raw_data)

    def _check_key(self, key):
        if len(key) * 8 != self.key_size:
            raise ValueError(
                'A key of size {} bits is required.'.format(self.key_size))

    def wrap(self, cek, headers, key):
        op_key = key.get_op_key('wrapKey')
        self._check_key(op_key)
        ek = aes_key_wrap(op_key, cek, default_backend())
        return ek

    def unwrap(self, ek, headers, key):
        op_key = key.get_op_key('unwrapKey')
        self._check_key(op_key)
        cek = aes_key_unwrap(op_key, ek, default_backend())
        return cek


class AESGCMAlgorithm(JWEAlgorithm):
    EXTRA_HEADERS = frozenset(['iv', 'tag'])

    def __init__(self, key_size):
        self.name = 'A{}GCMKW'.format(key_size)
        self.description = 'Key wrapping with AES GCM using {}-bit key'.format(key_size)
        self.key_size = key_size

    def prepare_key(self, raw_data):
        return OctKey.import_key(raw_data)

    def _check_key(self, key):
        if len(key) * 8 != self.key_size:
            raise ValueError(
                'A key of size {} bits is required.'.format(self.key_size))

    def wrap(self, cek, headers, key):
        op_key = key.get_op_key('wrapKey')
        self._check_key(op_key)

        #: https://tools.ietf.org/html/rfc7518#section-4.7.1.1
        #: The "iv" (initialization vector) Header Parameter value is the
        #: base64url-encoded representation of the 96-bit IV value
        iv_size = 96
        iv = os.urandom(iv_size // 8)

        cipher = Cipher(AES(op_key), GCM(iv), backend=default_backend())
        enc = cipher.encryptor()
        ek = enc.update(cek) + enc.finalize()

        h = {
            'iv': to_native(urlsafe_b64encode(iv)),
            'tag': to_native(urlsafe_b64encode(enc.tag))
        }
        return {'ek': ek, 'header': h}

    def unwrap(self, ek, headers, key):
        op_key = key.get_op_key('unwrapKey')
        self._check_key(op_key)

        iv = headers.get('iv')
        if not iv:
            raise ValueError('Missing "iv" in headers')

        tag = headers.get('tag')
        if not tag:
            raise ValueError('Missing "tag" in headers')

        iv = urlsafe_b64decode(to_bytes(iv))
        tag = urlsafe_b64decode(to_bytes(tag))

        cipher = Cipher(AES(op_key), GCM(iv, tag), backend=default_backend())
        d = cipher.decryptor()
        cek = d.update(ek) + d.finalize()
        return cek


class ECDHAlgorithm(JWEAlgorithm):
    def __init__(self, key_size=None):
        if key_size is None:
            self.name = 'ECDH-ES'
        else:
            self.name = 'ECDH-ES+A{}KW'.format(key_size)
        self.description = None
        self.key_size = key_size

    def prepare_key(self, raw_data):
        return ECKey.import_key(raw_data)

    def wrap(self, cek, headers, key):
        pass

    def unwrap(self, ek, headers, key):
        pass


JWE_ALG_ALGORITHMS = [
    RSAAlgorithm('RSA1_5', 'RSAES-PKCS1-v1_5', padding.PKCS1v15()),
    RSAAlgorithm(
        'RSA-OAEP', 'RSAES OAEP using default parameters',
        padding.OAEP(padding.MGF1(hashes.SHA1()), hashes.SHA1(), None)),
    RSAAlgorithm(
        'RSA-OAEP-256', 'RSAES OAEP using SHA-256 and MGF1 with SHA-256',
        padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None)),

    AESAlgorithm(128),  # A128KW
    AESAlgorithm(192),  # A192KW
    AESAlgorithm(256),  # A256KW
    AESGCMAlgorithm(128),  # A128GCMKW
    AESGCMAlgorithm(192),  # A192GCMKW
    AESGCMAlgorithm(256),  # A256GCMKW
]

# 'dir': '',
# 'ECDH-ES': '',
# 'ECDH-ES+A128KW': '',
# 'ECDH-ES+A192KW': '',
# 'ECDH-ES+A256KW': '',
# 'PBES2-HS256+A128KW': '',
# 'PBES2-HS384+A192KW': '',
# 'PBES2-HS512+A256KW': '',
