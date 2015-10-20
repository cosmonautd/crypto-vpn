from Crypto.Hash import SHA256
import os
from Crypto.Cipher import AES

def sha256(data, hexdigest=False):
    """
        Uses sha256 to has the input
    """
    sha = SHA256.new()
    sha.update(data)
    if hexdigest:
        return sha.hexdigest()
    else: return sha.digest()

BlockSize = 16
pad = lambda s: s + (BlockSize - len(s) % BlockSize) * bytes([BlockSize - len(s) % BlockSize])
"""
    Function that pads the AES message
"""
unpad = lambda s : s[:-ord(s[len(s)-1:])]
"""
    Function that unpads the AES message
"""

class AESCipher:
    def __init__( self, key ):
        self.key = key

    def encrypt( self, raw ):
        """
            Encrypts data using the provided AES key
        """
        raw = pad(raw)
        iv = os.urandom( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv ) #TODO: Are we really going to use CBC? Why?
        return iv + cipher.encrypt( raw )

    def decrypt( self, enc ):
        """
            Dencrypts data using the provided AES key
        """
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))
