import socket
import logging




MAX_PACKET = 1024

my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def main():
    client_connect = True
    try:
        my_socket.connect(('127.0.0.1', 6741))

        while client_connect:
            print('Choose mode: TIME , NAME , RAND , EXIT')
            user_input = input()
            logging.info(f'user has chosen mode {user_input}')

            if len(user_input) !=4:
                logging.error('Wrong number of bytes')
                print('Please enter 4 bytes')
                continue

            my_socket.send(user_input.encode())
            logging.info(f'user requested {user_input}')
            response = my_socket.recv(MAX_PACKET).decode()
            logging.info(f"user got response - {response}")
            print (response)

            if user_input == 'EXIT':
                logging.info('user chose EXIT')
                client_connect = False

    except socket.error as err:
        print('received socket error ' + str(err))

    finally:
        my_socket.close()
        logging.info('Closing ')


if __name__ == "__main__":
    logging.basicConfig(
        filename='2.6CLIENT.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()