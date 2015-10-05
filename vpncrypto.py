from Crypto.Hash import SHA256

def sha256(data, hexdigest=False):
    """
    """
    sha = SHA256.new()
    sha.update(data)
    if hexdigest:
        return sha.hexdigest()
    else: return sha.digest()
