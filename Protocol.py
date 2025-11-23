import struct
import logging
GLOB_LEN = 4
def send_message(sock, cmd, data):


    if isinstance(data, str):
        encoded_data = data.encode()
    else:
        encoded_data = data


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


def recv_message(sock):

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

        #IF BIN STAY(SS) ELSE decode
        if command == "SCREENSHOT":
            logging.info(f"command was {command}")
            return command, message
        else:
            logging.error(f"command was {command}")
            return command, message.decode()


    except Exception as err:
        logging.error(f"recv failed: {err}")
        return None, None



if __name__ == "__main__":
    logging.basicConfig(
        filename='2.7SERVER.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )