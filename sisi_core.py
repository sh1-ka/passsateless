from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json

FILE_VERSION = b'\x01' 

CHARACTER_SUBSETS = {
    "lowercase": "abcdefghijklmnopqrstuvwxyz",
    "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "digits": "0123456789",
    "symbols": "!#$%&()*+-./:;<=>?@[]^_{|}~",
}

def generate_password(master_key: str, login: str, service: str, pass_ver: int, lnth: int) -> str:
    if lnth > 75:
        raise ValueError("too long")

    raw_salt_string = f"{login}|{service}|{pass_ver}"
    raw_salt_bytes = raw_salt_string.encode("utf-8")

    digest = hashes.Hash(hashes.SHA256())
    digest.update(raw_salt_bytes)
    cur_salt = digest.finalize() 

    kdf = Argon2id(
        salt=cur_salt, 
        length=64,      
        iterations=4,
        lanes=4,
        memory_cost=2**19
    )
    
    raw_hash_bytes = kdf.derive(master_key.encode("utf-8"))

    alphabet = (
        CHARACTER_SUBSETS["lowercase"] +
        CHARACTER_SUBSETS["uppercase"] +
        CHARACTER_SUBSETS["digits"] +
        CHARACTER_SUBSETS["symbols"]
    )
    alphabet_length = len(alphabet)

    hash_int = int.from_bytes(raw_hash_bytes, byteorder='big')
    password = ""
    
    for _ in range(lnth):
        hash_int, char_index = divmod(hash_int, alphabet_length)
        password += alphabet[char_index]
        
    return password



def _get_hash_from_masterkey(master_key : str, salt : bytes):
    kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=4,
            lanes=4,
            memory_cost=2**19
            )
    return kdf.derive(master_key.encode("utf-8"))



def _write_data(master_key : str, data : dict, filename : str = "sisi.enc"):
    salt = os.urandom(16)
    nonce = os.urandom(12)
    
    key = _get_hash_from_masterkey(master_key, salt)
    aesgcm = AESGCM(key)
    json_bytes = json.dumps(data).encode('utf-8')
    encrypted_data = aesgcm.encrypt(nonce, json_bytes, None)
    
    tmp_filename = filename + ".tmp"
    with open(tmp_filename, "wb") as file:
        file.write(FILE_VERSION + salt + nonce + encrypted_data)
        file.flush()
        os.fsync(file.fileno())

    os.replace(tmp_filename, filename)

def _add_new_item(master_key : str, filename : str = "sisi.enc", login : str = "none", service : str = "none", pass_ver : int = 0, lnth : int = 15):
    data = _load_data(master_key, filename)

    data["content"].append({ 
        "login" : login,
        "service" : service,
        "pass_ver" : pass_ver,
        "lnth" : lnth
    })
    _write_data(master_key, data, filename)

def _delete_by_id(master_key: str, filename: str, id: int):
    data = _load_data(master_key, filename)
    
    if id < 0 or id >= len(data["content"]):
        raise IndexError("wrong id")
            
    data["content"].pop(id)
    _write_data(master_key, data, filename)


def _init_dict_file(master_key : str, filename : str):
    cur = {
        "content" : []
    }

    _write_data(master_key, cur, filename)


def _load_data(master_key : str, filename : str = "sisi.enc") -> dict:
    if not os.path.exists(filename):
        _init_dict_file(master_key, filename)

    with open(filename, "rb") as file:
        file_content = file.read()

    version = file_content[:1]
    if version != FILE_VERSION:
        raise ValueError(f"{version}")

    
    salt = file_content[1:17]
    nonce = file_content[17:29]
    encrypted_data = file_content[29:]
    
    key = _get_hash_from_masterkey(master_key, salt)
    aesgcm = AESGCM(key)
    
    try:
        decrypted_bytes = aesgcm.decrypt(nonce, encrypted_data, None)
        return json.loads(decrypted_bytes.decode('utf-8'))
    except Exception:
        raise ValueError("fail")
