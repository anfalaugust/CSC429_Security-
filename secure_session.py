
import json

from cryptography.fernet import Fernet, InvalidToken
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import BadSignature


class FernetSerializer:
    """Turns the session dict into an encrypted string and back."""

    def __init__(self, key):
        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def dumps(self, data):
        plaintext = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return self.fernet.encrypt(plaintext).decode("ascii")

    def loads(self, token, max_age=None):
        try:
            # ttl makes Fernet reject cookies older than the session lifetime
            plaintext = self.fernet.decrypt(token.encode("ascii"), ttl=max_age)
        except (InvalidToken, ValueError, TypeError):
            # Flask treats BadSignature as "invalid cookie" -> empty session
            raise BadSignature("Session cookie could not be decrypted.")
        return json.loads(plaintext)


class EncryptedCookieSessionInterface(SecureCookieSessionInterface):
    """Same behaviour as Flask's default session, but the cookie is encrypted."""

    def __init__(self, encryption_key):
        self.serializer_impl = FernetSerializer(encryption_key)

    def get_signing_serializer(self, app):
        return self.serializer_impl