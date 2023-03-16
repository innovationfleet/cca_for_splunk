"""Command line tool for encrypting/decrypting Splunk secrets"""
"""
The original code is developed by Hurricane Labs LLC under the
MIT license, see https://github.com/HurricaneLabs/splunksecrets
for original source code and additional functions that has been
stripped away in this version.

# Original License Notice from the README.md file in the original repo.
The MIT License (MIT)

Copyright (c) 2020 Hurricane Labs LLC

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
Software), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import algorithms, Cipher, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def b64decode(encoded):
    """Wrapper around `base64.b64decode` to add padding if necessary"""
    padding_len = 4 - (len(encoded) % 4)
    if padding_len < 4:
        encoded += "=" * padding_len
    return base64.b64decode(encoded)


def decrypt(secret, ciphertext):
    plaintext = "Ciphertext didn't match a Splunk Password starting with $7$: (" + ciphertext + ")"

    if ciphertext.startswith("$7$"):
        if len(secret) < 254:
            raise ValueError("secret too short, need 254 bytes, got %d" % len(secret))
        ciphertext = b64decode(ciphertext[3:])

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"disk-encryption",
            iterations=1,
            backend=default_backend()
        )
        key = kdf.derive(secret[:254])

        iv = ciphertext[:16]  # pylint: disable=invalid-name
        tag = ciphertext[-16:]
        ciphertext = ciphertext[16:-16]

        algorithm = algorithms.AES(key)
        cipher = Cipher(algorithm, mode=modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext).decode()
        print(plaintext)

    return plaintext

def encrypt(secret, plaintext, iv=None):  # pylint: disable=invalid-name
    if len(secret) < 254:
        raise ValueError("secret too short, need 254 bytes, got %d" % len(secret))

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"disk-encryption",
        iterations=1,
        backend=default_backend()
    )
    key = kdf.derive(secret[:254])

    if iv is None:
        iv = os.urandom(16)

    algorithm = algorithms.AES(key)
    cipher = Cipher(algorithm, mode=modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()

    return "$7$%s" % base64.b64encode(b"%s%s%s" % (iv, ciphertext, encryptor.tag)).decode()


def main():
    """Command line interface"""
    cliargs = argparse.ArgumentParser()

    cliargs.add_argument("--splunk-secret", dest="secret")
    cliargs.add_argument("--ciphertext", dest="ciphertext")
    cliargs.add_argument("--cleartext", dest="cleartext")

    args = cliargs.parse_args()

    try:
        if args.ciphertext:
            output = decrypt(args.secret.encode('ascii'), args.ciphertext)
        elif args.cleartext:
            output = encrypt(args.secret.encode('ascii'), args.cleartext)
    except KeyboardInterrupt:
        pass
    else:
        print(output)

if __name__ == "__main__":
    main()