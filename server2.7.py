"""
Author: Guy Carmeli
Date: 13/11/2025
Description:Creates a server that recives a set command from user and returns a value.
"""

import socket
import logging
import glob
import os
import shutil
import subprocess
import pyautogui
import Protocol2.7


QUEUE_LEN = 1
MAX_PACKET= 1024


def dir_path(user_dir):
    try:
        files_list =glob.glob(f"{user_dir}/*")
        logging.info("path of user dir located")
        return files_list
    except OSError:
        return ['file not found']


def dir_remove(user_file):
    try:
        os.remove(user_file)
        return " files removed"
    except OSError:
        return "file not found"


def copy_files(copy_from, copy_to):
    try:
        shutil.copy(copy_from, copy_to)
        return " copied file"
    except OSError:
        return "file not found"


def execute_files(user_file_exe):
        try:
          if  subprocess.call(user_file_exe) == 0:
            return f"{user_file_exe} executed successfully"
          else:
            return f"{user_file_exe} Failed to execute"
        except Exception as err:
            return f"file not found: {err}"


def take_screenshot():
    try:
        image = pyautogui.screenshot()
        image.save(r'screenshot.jpg')
        return "image saved"
    except Exception as err:
        return f"failed to save screenshot: {err}"


def send_screenshot():
    try:
        with open('screenshot.jpg', 'rb') as screenshot:
            screenshot_bytes = screenshot.read()
        return screenshot_bytes
    except Exception as err:
        return f"failed to save screenshot: {err}"


def exit_fucntion(client_socket):
    try:
        client_socket.close()
        return "existed server"
    except Exception as err:
        return f"failed to close client: {err}"

def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.bind(('0.0.0.0', 6741))
        my_socket.listen(QUEUE_LEN)

        while True:
            client_socket, client_address = my_socket.accept()
            logging.info('Client connected')

            try:
                while True:
                    request_bytes = recv_message(client_socket)
                    if not request_bytes:
                        break
                    request = request_bytes.decode()

                    if request.startswith("DIR"):
                        path_without_command = request[4:].strip()
                        files_list = dir_path(path_without_command)
                        response_to_user = "\n".join(files_list)
                        send_message(client_socket, response_to_user.encode())

                    elif request == 'EXIT':
                        response_to_user = exit_fucntion(client_socket)
                        logging.info("exited server")
                        send_message(client_socket, response_to_user.encode())
                        break

                    else:
                        wrong_request = request + ' is not a valid command'
                        send_message(client_socket, wrong_request.encode())
                        logging.warning('user sent unavailable request')

            except socket.error as err:
                logging.error('received socket error on client socket ' + str(err))

            finally:
                client_socket.close()

    except socket.error as err:
        print('received socket error on server socket ' + str(err))

    finally:
        my_socket.close()





if __name__ == "__main__":
    logging.basicConfig(
        filename='2.7SERVER.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()