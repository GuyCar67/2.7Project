import socket
import logging
import Protocol



MAX_PACKET = 1024
SERVER_IP = "127.0.0.1"
SERVER_PORT = 6741


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.connect((SERVER_IP, SERVER_PORT))
        logging.info("connected to server")
        while True:
            user_input = input("Enter command:"
                               "DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT <path>:"
                               "Enter HELP for detailed help")
            Protocol.send_message(my_socket, user_input)
            logging.info(f'user has chosen mode {user_input}')

            cmd, data = Protocol.recv_message(my_socket)
            if cmd is None:
                logging.info("user disconnected")
                break

            if cmd == "SCREENSHOT":
                with open("received_screenshot.jpg", "wb") as f:
                    f.write(data)
                print("Screenshot saved.")
            else:
                print(cmd)


    except socket.error as err:
        print('received socket error ' + str(err))
        logging.critical("socket error")
    finally:
        my_socket.close()
        logging.info('Closing ')


if __name__ == "__main__":
    logging.basicConfig(
        filename='2.7CLIENT.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()