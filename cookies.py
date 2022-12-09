# %%
import sqlite3
from hashlib import pbkdf2_hmac
from Cryptodome.Cipher import AES
import keyring
import json

from config import cookies_path, host_key

# %%
# https://github.com/Noskthing/Scripts/blob/master/getChromeCookies_macOS.py


def get_password_from_keychain(browser='Microsoft Edge'):
    """Try to read password from keychain
    Args:
        isChrome will help judge what name is
        if it' true name is Chrome else Chromium
    Return:
        password storage in keychain
    """
    return keyring.get_password(browser + ' Safe Storage', browser)


encrypted_key = get_password_from_keychain()


# %%
def get_cookies_erncrypt_key():
    """Generates a newly allocated SymmetricKey object based on the password found
    in the Keychain.  The generated key is for AES encryption.
    Return:
       SymmetricKey for AES 
    """
    # Constant for Symmetic key derivation.
    CHROME_COOKIES_ENCRYPTION_ITERATIONS = 1003

    # Salt for Symmetric key derivation.
    CHROME_COOKIES_ENCRYPTION_SALT = b'saltysalt'

    # Key size required for 128 bit AES. So dklen = 128/8
    CHROME_COOKIES_ENCRYPTION_DKLEN = 16

    return pbkdf2_hmac(hash_name='sha1',
                       password=encrypted_key.encode('utf8'),
                       salt=CHROME_COOKIES_ENCRYPTION_SALT,
                       iterations=CHROME_COOKIES_ENCRYPTION_ITERATIONS,
                       dklen=CHROME_COOKIES_ENCRYPTION_DKLEN)


def decrypt(encrypted_value):
    encrypt_string = encrypted_value[3:]
    cipher = AES.new(get_cookies_erncrypt_key(), AES.MODE_CBC, IV=b' ' * 16)
    decrypted_string = cipher.decrypt(encrypt_string)
    return decrypted_string.decode('utf8').rstrip('\x10\x01\x0b\r')


# %%

conn = sqlite3.connect(cookies_path)
c = conn.cursor()
cursor = c.execute(
    'select host_key, path, expires_utc, name, value, encrypted_value from cookies where host_key = ?',
    (host_key, ))

cookies = {}
for host_key, path, expires_utc, name, value, encrypted_value in cursor:
    # print(host_key, path, expires_utc, name, value, encrypted_value)
    cookies[name] = decrypt(encrypted_value)
conn.close()

# %%
with open('cache.json', 'w') as f:
    json.dump(cookies, f)
