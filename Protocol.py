import struct
import logging

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet


class Encryption:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.fernet_key = None

    def generate_rsa_keys(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        logging.info("RSA: generated 2048-bit key pair")

    def serialize_public_key(self):
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    @staticmethod
    def load_public_key(pem_bytes):
        return serialization.load_pem_public_key(pem_bytes)

    @staticmethod
    def rsa_encrypt(public_key, data):
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        logging.info(f"RSA: encrypted symmetric key with public key -> {len(encrypted)} bytes: {encrypted[:24].hex()}...")
        return encrypted

    def rsa_decrypt(self, data):
        decrypted = self.private_key.decrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        logging.info(f"RSA: decrypted symmetric key with private key -> {len(decrypted)} bytes")
        return decrypted

    @staticmethod
    def new_fernet_key():
        key = Fernet.generate_key()
        logging.info("FERNET: generated new session key")
        return key

    def encrypt(self, plaintext):
        token = Fernet(self.fernet_key).encrypt(plaintext)
        logging.info(f"FERNET ENCRYPT: {len(plaintext)} plain bytes -> {len(token)} cipher bytes: {token[:32].decode(errors='replace')}...")
        return token

    def decrypt(self, token):
        plaintext = Fernet(self.fernet_key).decrypt(token)
        logging.info(f"FERNET DECRYPT: {len(token)} cipher bytes -> {len(plaintext)} plain bytes")
        return plaintext


class Protocol:
    GLOB_LEN = 4
    BINARY_COMMANDS = {"SCREENSHOT", "PUBKEY", "AESKEY"}

    def __init__(self, sock, encryption=None):
        self.sock = sock
        self.encryption = encryption

    def _ready(self):
        return self.encryption is not None and self.encryption.fernet_key is not None

    def _recv_exact(self, amount):
        buffer = b''
        while len(buffer) < amount:
            temp = self.sock.recv(min(amount - len(buffer), 4096))
            if not temp:
                return None
            buffer += temp
        return buffer

    def send_message(self, cmd, data):
        if isinstance(data, str):
            encoded_data = data.encode()
        else:
            encoded_data = data

        if self._ready():
            encoded_data = self.encryption.encrypt(encoded_data)

        encoded_cmd = cmd.encode()
        cmd_len = struct.pack("I", len(encoded_cmd))
        data_len = struct.pack("I", len(encoded_data))
        full_message = cmd_len + encoded_cmd + data_len + encoded_data

        sent = 0
        while sent < len(full_message):
            try:
                message_sent = self.sock.send(full_message[sent::])
                if message_sent == 0:
                    logging.error("socket connection broken")
                    return None, None
                sent += message_sent
            except Exception as err:
                print("send failed", err)
                logging.error("send failed client disconected")
                return None, None
        return None

    def recv_message(self):
        try:
            cmd_len_bytes = self._recv_exact(self.GLOB_LEN)
            if cmd_len_bytes is None:
                logging.error("exited mid connection")
                return None, None
            command_length = struct.unpack("I", cmd_len_bytes)[0]

            command = self._recv_exact(command_length)
            if command is None:
                logging.error("Connection closed while receiving command")
                return None, None

            data_len_bytes = self._recv_exact(self.GLOB_LEN)
            if data_len_bytes is None:
                logging.error("Connection closed while receiving data length")
                return None, None
            message_length = struct.unpack("I", data_len_bytes)[0]

            message = self._recv_exact(message_length)
            if message is None:
                logging.error("Connection closed while receiving data")
                return None, None

            command = command.decode()

            if self._ready():
                message = self.encryption.decrypt(message)

            if command in self.BINARY_COMMANDS:
                logging.info(f"command was {command}")
                return command, message
            else:
                logging.error(f"command was {command}")
                return command, message.decode()

        except Exception as err:
            logging.error(f"recv failed: {err}")
            return None, None

    def server_handshake(self):
        try:
            self.encryption.generate_rsa_keys()
            self.send_message("PUBKEY", self.encryption.serialize_public_key())
            cmd, enc_key = self.recv_message()
            if cmd != "AESKEY" or enc_key is None:
                logging.error("HANDSHAKE: did not receive the symmetric key")
                return False
            self.encryption.fernet_key = self.encryption.rsa_decrypt(enc_key)
            logging.info("HANDSHAKE: Fernet key established (server)")
            return True
        except Exception as err:
            logging.error(f"HANDSHAKE failed (server): {err}")
            return False

    def client_handshake(self):
        try:
            cmd, pub_pem = self.recv_message()
            if cmd != "PUBKEY" or pub_pem is None:
                logging.error("HANDSHAKE: did not receive PUBKEY")
                return False
            public_key = self.encryption.load_public_key(pub_pem)
            key = self.encryption.new_fernet_key()
            self.send_message("AESKEY", self.encryption.rsa_encrypt(public_key, key))
            self.encryption.fernet_key = key
            logging.info("HANDSHAKE: Fernet key established (client)")
            return True
        except Exception as err:
            logging.error(f"HANDSHAKE failed (client): {err}")
            return False
