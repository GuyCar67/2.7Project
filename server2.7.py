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
from re import search

import pyautogui
import Protocol


QUEUE_LEN = 1
MAX_PACKET= 1024


def dir_path(user_dir):
    try:
        files_list =glob.glob(f"{user_dir}/*")
        logging.info("path of user dir located")
        return files_list
    except OSError:
        return ['file not found']


def remove_file(user_file):
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
        return "files not found"


def execute_files(user_file_exe):
        try:
          if  subprocess.call(user_file_exe):
            return f"{user_file_exe} is executable"
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


def exit_function(client_socket):
    try:
        client_socket.close()
    except Exception as err:
        logging.error("failed to close client:" ,{err})


def help_function(data):
    if data == "DIR":
        return "DIR <path>: lists all files in the specified directory."

    elif data == "REMOVE":
        return "REMOVE <file_path.<extension>>: deletes the specified file."

    elif data == "COPY":
        return "COPY <source_path>.<extension> <destination_path>.<extension>: copies a file from source to destination."

    elif data == "EXECUTE":
        return "EXECUTE <file_path>.<executble-extension>: runs the specified script."

    elif data == "SCREENSHOT":
        return "SCREENSHOT: takes a screenshot and sends it to client."

    elif data == "EXIT":
        return "EXIT: closes the connection to the server."

    elif data == "HELP":
        return "HELP <command>: shows usage information for the given command."

    else:
        return f"no help available for '{data}' try-DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT"




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
                    cmd , data = Protocol.recv_message(client_socket)
                    if cmd is None:
                        break

                    if cmd == "DIR":
                        files_list = dir_path(data)
                        response_to_user = "\n".join(files_list)
                        Protocol.send_message(client_socket,  response_to_user)

                    elif cmd == "REMOVE":
                        response_to_user = remove_file(data)
                        Protocol.send_message(client_socket,  response_to_user)

                    elif cmd == "COPY":
                        src, dest = data.split(" ",1)
                        response_to_user = copy_files(src, dest)
                        Protocol.send_message(client_socket, response_to_user)

                    elif cmd == "EXECUTE":
                        response_to_user = execute_files(data)
                        Protocol.send_message(client_socket, response_to_user)

                    elif cmd == "SCREENSHOT":
                        take_screenshot()
                        response_to_user = send_screenshot()
                        Protocol.send_message(client_socket,response_to_user)

                    elif cmd == "EXIT":
                        exit_function(client_socket)
                        logging.info('client has exited')
                        break

                    elif cmd == "HELP":
                        response_to_user = help_function(data)
                        Protocol.send_message(client_socket, response_to_user)

                    else:
                        response_to_user ="invalid command, please try again(DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT)"
                        Protocol.send_message(client_socket, response_to_user)

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