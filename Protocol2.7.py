import struct
import logging
import socket
GLOB_LEN = 4
def send_message(sock, msg):
    # Remove leading/trailing whitespace
    msg = msg.strip()

    # Split into command and data (first word = command, rest = data)
    parts = msg.split(" ", 1)
    if len(parts) == 1:
        cmd = parts[0]
        data =""
    else:
        cmd = parts[0]
        data = parts[1]

    encoded_cmd = cmd.encode()
    encoded_data = data.encode()

    # Pack lengths as 4-byte unsigned integers (network byte order)
    cmd_len = struct.pack("I", len(encoded_cmd))
    data_len = struct.pack("I", len(encoded_data))

    full_message = cmd_len + encoded_cmd + data_len + encoded_data
    sent = b''
    while len(sent) < len(full_message):
        try:
            message_sent = sock.send(full_message[sent::])
            sent += message_sent
        except Exception as err:
            print("send failed", err)
            logging.warning("send failed client disconected")
            break


def recv_message(sock):
    temp_len = b''
    while len(temp_len) < GLOB_LEN:
        temp_len += sock.recv(GLOB_LEN - len(temp_len))
        if temp_len == b"":
            logging.warning("closed while receiving message")
            break
    if temp_len != b"":
        message_length = struct.unpack("I", temp_len)[0]
        message = b''
        while len(message) < message_length:
            message += sock.recv(message_length - len(message))
    else:
        message = temp_len
    return message

if __name__ == "__main__":
    logging.basicConfig(
        filename='2.7SERVER.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
