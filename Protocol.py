import struct
import logging

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet

GLOB_LEN = 4

# commands whose DATA is raw bytes and must NOT be .decode()'d after receiving
BINARY_COMMANDS = {"SCREENSHOT", "PUBKEY", "AESKEY"}


# ---------------------------------------------------------------------------
# RSA  (asymmetric: used ONCE in the handshake to protect the Fernet key)
# ---------------------------------------------------------------------------
def generate_rsa_keys():
    """
    creates a fresh RSA key pair for the server
    param: None
    return: (private_key, public_key)
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def serialize_public_key(public_key):
    """
    turns a public key into PEM bytes so it can be sent over the socket
    param public_key:
    return: bytes (PEM)
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_public_key(pem_bytes):
    """
    rebuilds a public key object from the PEM bytes received from the server
    param pem_bytes:
    return: public_key object
    """
    return serialization.load_pem_public_key(pem_bytes)


def rsa_encrypt(public_key, data):
    """
    encrypts data (the Fernet key) with the server's public key
    param public_key, data(bytes):
    return: bytes -> encrypted
    """
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def rsa_decrypt(private_key, data):
    """
    decrypts the Fernet key with the server's private key
    param private_key, data(bytes):
    return: bytes -> the Fernet key
    """
    return private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


# ---------------------------------------------------------------------------
# Fernet  (symmetric: used for every message AFTER the handshake)
# A Fernet key is 32 random bytes, url-safe-base64 encoded (44 bytes).
# ---------------------------------------------------------------------------
def generate_fernet_key():
    """
    creates a random Fernet session key (the two-way key the client generates)
    param: None
    return: bytes
    """
    return Fernet.generate_key()


def fernet_encrypt(key, plaintext):
    """
    encrypts a payload with Fernet
    param key(bytes), plaintext(bytes):
    return: bytes -> token
    """
    return Fernet(key).encrypt(plaintext)


def fernet_decrypt(key, token):
    """
    decrypts a Fernet token. no ttl is passed -> no timestamp verification
    param key(bytes), token(bytes):
    return: bytes -> plaintext
    """
    return Fernet(key).decrypt(token)


# ---------------------------------------------------------------------------
# Protocol framing : [len(cmd)][cmd][len(data)][data]
# When fernet_key is given, the DATA field is encrypted (the cmd stays plain
# so recv still knows whether the payload is text or raw bytes).
# ---------------------------------------------------------------------------
def send_message(sock, cmd, data, fernet_key=None):
    """
    sends a message and builds a protcol consisting of len(cmd)cmdlen(data)data
    if fernet_key is given, the data field is encrypted with Fernet first
    param sock,cmd,data,fernet_key:
    return:None
    """

    if isinstance(data, str):
        encoded_data = data.encode()
    else:
        encoded_data = data

    if fernet_key is not None:
        encoded_data = fernet_encrypt(fernet_key, encoded_data)

    encoded_cmd = cmd.encode()
    cmd_len = struct.pack("I", len(encoded_cmd))
    data_len = struct.pack("I", len(encoded_data))
    full_message = cmd_len + encoded_cmd + data_len + encoded_data

    sent = 0
    while sent < len(full_message):
        try:
            message_sent = sock.send(full_message[sent::])
            if message_sent == 0:
                logging.error("socket connection broken")
                return None, None
            sent += message_sent
        except Exception as err:
            print("send failed", err)
            logging.error("send failed client disconected")
            return None, None
    return None


def recv_message(sock, fernet_key=None):
    """
    receives a message form user and reads 4 first bytes, and then reads the amount in those 4 bytes twice sends the message without the protcol in txt,txt/txt,bin
    if fernet_key is given, the data field is Fernet-decrypted before being returned
    param sock,fernet_key:
    return:None/command,data
    """

    try:
        cmd_len_bytes = b''
        while len(cmd_len_bytes) < GLOB_LEN:
            temp = sock.recv(GLOB_LEN - len(cmd_len_bytes))
            if not temp:
                logging.error("exited mid connection")
                return None, None
            cmd_len_bytes += temp

        command_length = struct.unpack("I", cmd_len_bytes)[0]
        command = b''
        while len(command) < command_length:
            temp = sock.recv(command_length - len(command))
            if not temp:
                logging.error("Connection closed while receiving command")
                return None, None
            command += temp

        data_len_bytes = b''
        while len(data_len_bytes) < GLOB_LEN:
            temp = sock.recv(GLOB_LEN - len(data_len_bytes))
            if not temp:
                logging.error("Connection closed while receiving data length")
                return None, None
            data_len_bytes += temp

        message_length = struct.unpack("I", data_len_bytes)[0]

        message = b''
        while len(message) < message_length:
            temp = sock.recv(min(message_length - len(message), 4096))
            if not temp:
                logging.error("Connection closed while receiving data")
                return None, None
            message += temp

        #ALWAYS DECODE CMD
        command = command.decode()

        #DECRYPT the data field if we already share a Fernet key
        if fernet_key is not None:
            message = fernet_decrypt(fernet_key, message)

        #IF BIN STAY(SS) ELSE decode
        if command in BINARY_COMMANDS:
            logging.info(f"command was {command}")
            return command, message
        else:
            logging.error(f"command was {command}")
            return command, message.decode()


    except Exception as err:
        logging.error(f"recv failed: {err}")
        return None, None


# ---------------------------------------------------------------------------
# Handshake helpers (hybrid RSA + Fernet key exchange)
# ---------------------------------------------------------------------------
def server_handshake(sock):
    """
    SERVER side: make an RSA pair, send the PUBLIC key, receive the Fernet key
    encrypted with it, decrypt it with the PRIVATE key.
    param sock:
    return: bytes (shared Fernet key) / None on failure
    """
    try:
        private_key, public_key = generate_rsa_keys()
        send_message(sock, "PUBKEY", serialize_public_key(public_key))

        cmd, enc_key = recv_message(sock)
        if cmd != "AESKEY" or enc_key is None:
            logging.error("HANDSHAKE: did not receive the symmetric key")
            return None

        fernet_key = rsa_decrypt(private_key, enc_key)
        logging.info("HANDSHAKE: Fernet key established (server)")
        return fernet_key
    except Exception as err:
        logging.error(f"HANDSHAKE failed (server): {err}")
        return None


def client_handshake(sock):
    """
    CLIENT side: receive the server's PUBLIC key, make a random Fernet key,
    encrypt it with the public key, send it back.
    param sock:
    return: bytes (shared Fernet key) / None on failure
    """
    try:
        cmd, pub_pem = recv_message(sock)
        if cmd != "PUBKEY" or pub_pem is None:
            logging.error("HANDSHAKE: did not receive PUBKEY")
            return None

        public_key = load_public_key(pub_pem)
        fernet_key = generate_fernet_key()
        enc_key = rsa_encrypt(public_key, fernet_key)
        send_message(sock, "AESKEY", enc_key)
        logging.info("HANDSHAKE: Fernet key established (client)")
        return fernet_key
    except Exception as err:
        logging.error(f"HANDSHAKE failed (client): {err}")
        return None


if __name__ == "__main__":
    logging.basicConfig(
        filename='2.7SERVER.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
