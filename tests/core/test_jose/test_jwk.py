import unittest
from authlib.jose import jwk
from authlib.common.encoding import base64_to_int
from tests.util import read_file_path

RSA_PRIVATE_KEY = read_file_path('jwk_private.json')


class JWKTest(unittest.TestCase):
    def assertBase64IntEqual(self, x, y):
        self.assertEqual(base64_to_int(x), base64_to_int(y))

    def test_ec_public_key(self):
        # https://tools.ietf.org/html/rfc7520#section-3.1
        obj = read_file_path('ec_public.json')
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key)
        self.assertEqual(new_obj['crv'], obj['crv'])
        self.assertBase64IntEqual(new_obj['x'], obj['x'])
        self.assertBase64IntEqual(new_obj['y'], obj['y'])

    def test_ec_private_key(self):
        # https://tools.ietf.org/html/rfc7520#section-3.2
        obj = read_file_path('ec_private.json')
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key, 'EC')
        self.assertEqual(new_obj['crv'], obj['crv'])
        self.assertBase64IntEqual(new_obj['x'], obj['x'])
        self.assertBase64IntEqual(new_obj['y'], obj['y'])
        self.assertBase64IntEqual(new_obj['d'], obj['d'])

    def test_invalid_ec(self):
        self.assertRaises(ValueError, jwk.loads, {'kty': 'EC'})
        self.assertRaises(ValueError, jwk.dumps, '', 'EC')

    def test_rsa_public_key(self):
        # https://tools.ietf.org/html/rfc7520#section-3.3
        obj = read_file_path('jwk_public.json')
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key)
        self.assertBase64IntEqual(new_obj['n'], obj['n'])
        self.assertBase64IntEqual(new_obj['e'], obj['e'])

    def test_rsa_private_key(self):
        # https://tools.ietf.org/html/rfc7520#section-3.4
        obj = RSA_PRIVATE_KEY
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key, 'RSA')
        self.assertBase64IntEqual(new_obj['n'], obj['n'])
        self.assertBase64IntEqual(new_obj['e'], obj['e'])
        self.assertBase64IntEqual(new_obj['d'], obj['d'])
        self.assertBase64IntEqual(new_obj['p'], obj['p'])
        self.assertBase64IntEqual(new_obj['q'], obj['q'])
        self.assertBase64IntEqual(new_obj['dp'], obj['dp'])
        self.assertBase64IntEqual(new_obj['dq'], obj['dq'])
        self.assertBase64IntEqual(new_obj['qi'], obj['qi'])

    def test_rsa_private_key2(self):
        obj = {
            "kty": "RSA",
            "kid": "bilbo.baggins@hobbiton.example",
            "use": "sig",
            "n": RSA_PRIVATE_KEY['n'],
            'd': RSA_PRIVATE_KEY['d'],
            "e": "AQAB"
        }
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key.raw_key, 'RSA')
        self.assertBase64IntEqual(new_obj['n'], obj['n'])
        self.assertBase64IntEqual(new_obj['e'], obj['e'])
        self.assertBase64IntEqual(new_obj['d'], obj['d'])
        self.assertBase64IntEqual(new_obj['p'], RSA_PRIVATE_KEY['p'])
        self.assertBase64IntEqual(new_obj['q'], RSA_PRIVATE_KEY['q'])
        self.assertBase64IntEqual(new_obj['dp'], RSA_PRIVATE_KEY['dp'])
        self.assertBase64IntEqual(new_obj['dq'], RSA_PRIVATE_KEY['dq'])
        self.assertBase64IntEqual(new_obj['qi'], RSA_PRIVATE_KEY['qi'])

    def test_invalid_rsa(self):
        obj = {
            "kty": "RSA",
            "kid": "bilbo.baggins@hobbiton.example",
            "use": "sig",
            "n": RSA_PRIVATE_KEY['n'],
            'd': RSA_PRIVATE_KEY['d'],
            'p': RSA_PRIVATE_KEY['p'],
            "e": "AQAB"
        }
        self.assertRaises(ValueError, jwk.loads, obj)
        self.assertRaises(ValueError, jwk.loads, {'kty': 'RSA'})
        self.assertRaises(ValueError, jwk.dumps, '', 'RSA')

    def test_dumps_okp_public_key(self):
        key = read_file_path('ed25519-ssh.pub')
        self.assertRaises(ValueError, jwk.dumps, key)

        obj = jwk.dumps(key, 'OKP')
        self.assertEqual(obj['kty'], 'OKP')
        self.assertEqual(obj['crv'], 'Ed25519')

        key = read_file_path('ed25519-pub.pem')
        obj = jwk.dumps(key, 'OKP')
        self.assertEqual(obj['kty'], 'OKP')
        self.assertEqual(obj['crv'], 'Ed25519')

    def test_loads_okp_public_key(self):
        obj = {
            "x": "AD9E0JYnpV-OxZbd8aN1t4z71Vtf6JcJC7TYHT0HDbg",
            "crv": "Ed25519",
            "kty": "OKP"
        }
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key)
        self.assertEqual(obj['x'], new_obj['x'])

    def test_dumps_okp_private_key(self):
        key = read_file_path('ed25519-pkcs8.pem')
        obj = jwk.dumps(key, 'OKP')
        self.assertEqual(obj['kty'], 'OKP')
        self.assertEqual(obj['crv'], 'Ed25519')
        self.assertIn('d', obj)

    def test_loads_okp_private_key(self):
        obj = {
            'x': '11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo',
            'd': 'nWGxne_9WmC6hEr0kuwsxERJxWl7MmkZcDusAxyuf2A',
            'crv': 'Ed25519',
            'kty': 'OKP'
        }
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key)
        self.assertEqual(obj['d'], new_obj['d'])

    def test_mac_computation(self):
        # https://tools.ietf.org/html/rfc7520#section-3.5
        obj = {
            "kty": "oct",
            "kid": "018c0ae5-4d9b-471b-bfd6-eef314bc7037",
            "use": "sig",
            "alg": "HS256",
            "k": "hJtXIZ2uSN5kbQfbtTNWbpdmhkV8FJG-Onbc6mxCcYg"
        }
        key = jwk.loads(obj)
        new_obj = jwk.dumps(key)
        self.assertEqual(obj['k'], new_obj['k'])
        self.assertIn('use', new_obj)

        new_obj = jwk.dumps(key, use='sig')
        self.assertEqual(new_obj['use'], 'sig')

    def test_jwk_loads(self):
        self.assertRaises(ValueError, jwk.loads, {})
        self.assertRaises(ValueError, jwk.loads, {}, 'k')

        obj = {
            "kty": "oct",
            "kid": "018c0ae5-4d9b-471b-bfd6-eef314bc7037",
            "use": "sig",
            "alg": "HS256",
            "k": "hJtXIZ2uSN5kbQfbtTNWbpdmhkV8FJG-Onbc6mxCcYg"
        }
        self.assertRaises(ValueError, jwk.loads, [obj], 'invalid-kid')

    def test_jwk_dumps_ssh(self):
        key = read_file_path('ssh_public.pem')
        obj = jwk.dumps(key, kty='RSA')
        self.assertEqual(obj['kty'], 'RSA')
