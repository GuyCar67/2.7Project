import socket
import logging
import Protocol



MAX_PACKET = 1024
SERVER_IP = "127.0.0.1"
SERVER_PORT = 6741
COMMAND_LIST = ["DIR","REMOVE","COPY","EXECUTE","SCREENSHOT","EXIT","HELP"]

def main():
    """
    connects to a server and sends requests and receives request
    """
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.connect((SERVER_IP, SERVER_PORT))
        logging.info("connected to server")
        while True:
            user_cmd = input("Enter command:"
                               "DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT"
                               "Enter HELP for detailed help")
            while user_cmd not in COMMAND_LIST:
                user_cmd = input("Enter command:"
                                 "DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT"
                                 "Enter HELP for detailed help")
            if user_cmd not in ["SCREENSHOT", "EXIT",]:
                if user_cmd == "HELP":
                    logging.info(f"user command was {user_cmd}")
                    user_data = input("Please enter cmd you want to recive instructions on.")
                else:
                    user_data = input("Please enter <path>/")
            else:
                user_data = ""
            Protocol.send_message(my_socket, user_cmd,user_data )
            logging.info(f'user has chosen mode {user_cmd}')

            cmd, data = Protocol.recv_message(my_socket)
            if cmd is None:
                logging.error("Server disconnected")
                break
            if cmd == "SCREENSHOT":
                with open('screenshot_after_print.jpg', 'wb') as f:
                    f.write(data)
                print('Screenshot saved as "screenshot_received.jpg"')
                logging.info(f'screenshot was saved as "screenshot_received.jpg"')
            else:
                print(f"{data}")






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