import struct
import logging
GLOB_LEN = 4
def send_message(sock, msg):

    msg = msg.strip()
    parts = msg.split(" ", 1)
    if len(parts) == 1:
        cmd = parts[0]
        data =""
    else:
        cmd = parts[0]
        data = parts[1]

    encoded_cmd = cmd.encode()
    encoded_data = data.encode()
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
            logging.warning("send failed client disconected")
            return None, None
    return None


def recv_message(sock):

    try:
        cmd_len_bytes = b''
        while len(cmd_len_bytes) < GLOB_LEN:
            temp = sock.recv(GLOB_LEN - len(cmd_len_bytes))
            if not temp:
                logging.warning("exited mid connection")
                return None, None
            cmd_len_bytes += temp

        command_length = struct.unpack("I", cmd_len_bytes)[0]
        command = b''
        while len(command) < command_length:
            temp = sock.recv(command_length - len(command))
            if not temp:
                logging.warning("Connection closed while receiving command")
                return None, None
            command += temp

        data_len_bytes = b''
        while len(data_len_bytes) < GLOB_LEN:
            temp = sock.recv(GLOB_LEN - len(data_len_bytes))
            if not temp:
                logging.warning("Connection closed while receiving data length")
                return None, None
            data_len_bytes += temp

        message_length = struct.unpack("I", data_len_bytes)[0]

        message = b''
        while len(message) < message_length:
            temp = sock.recv(min(message_length - len(message), 4096))
            if not temp:
                logging.warning("Connection closed while receiving data")
                return None, None
            message += temp
        #ALWAYS DECODE CMD
        command = command.decode()

        #IF BIN STAY(SS) ELSE decode
        if command == "BIN":
            return command, message
        else:
            return command, message.decode()


    except Exception as err:
        logging.error(f"recv failed: {err}")
        return None, None


def send_response(sock, data):

    try:
        if isinstance(data, bytes):
            encoded_cmd = b"BIN"
            encoded_data = data
        else:
            encoded_cmd = b"TXT"
            encoded_data = data.encode()

        cmd_len = struct.pack("I", len(encoded_cmd))
        data_len = struct.pack("I", len(encoded_data))

        full_message = cmd_len + encoded_cmd + data_len + encoded_data

        sent = 0
        while sent < len(full_message):
            message_sent = sock.send(full_message[sent:])
            if message_sent == 0:
                return False
            sent += message_sent
        return True

    except Exception as err:
        logging.error(f"send response func failed: {err}")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        filename='2.7SERVER.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )