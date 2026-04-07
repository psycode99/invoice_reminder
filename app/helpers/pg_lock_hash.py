import hashlib

def lock_key(value: str) -> int:
    return int(hashlib.sha256(value.encode()).hexdigest(), 16) % (2**63)