from cryptography.fernet import Fernet

from model_types.environ_conf import EnvConf

ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

# 復号化関数
async def decrypt_password(encrypted_password:bytes) -> str:
    """
    byte列の文字の復号化

    Args:
        encrypted_password (bytes): 復号化する文字列

    Returns:
        str: 復号化した文字
    """
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        decrypted_password = cipher_suite.decrypt(encrypted_password)
        return decrypted_password.decode('utf-8')
    # トークンが無効の場合
    except:
        return ''

# 暗号化関数
async def encrypt_password(password:str) -> bytes:
    """
    文字の暗号化

    Args:
        password (str): 暗号化する文字列

    Returns:
        bytes: 暗号化した文字列
    """
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
        return encrypted_password
    except:
        return b''