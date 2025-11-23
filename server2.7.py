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
import Protocol


QUEUE_LEN = 1
MAX_PACKET= 1024
SERVER_IP = "127.0.0.1"
SERVER_PORT = 6741


def dir_path(user_dir):
    """
    gives the user a directory path,infront of their input
    param user_dir:
    return: list of path of dir
    """
    try:
        files_list =glob.glob(f"{user_dir}/*")
        logging.info("DIR:path of user dir located")
        return files_list
    except OSError:
        logging.error("DIR:path of dir not ffound")
        return ['file not found']


def remove_file(user_file):
    """
    removes a file the user has chose
    param user_file:
    return:str
    """
    try:
        os.remove(user_file)
        logging.info(f"REMOVE:removed {user_file}")
        return " files removed"
    except OSError:
        logging.error("REMOVE: file not found")
        return "file not found"


def copy_files(copy_from, copy_to):
    """
    copies a file from src to dest
    param copy_from,copy_to:
    return: string -sucssefull/unsucssesfull
    """
    try:
        shutil.copy(copy_from, copy_to)
        logging.info(f"COPY:copied {copy_from} to {copy_to}")
        return " copied file"
    except OSError:
        logging.error("COPY: file not found")
        return "files not found"


def execute_files(user_file_exe):
    """
    checks if a file is executable
    param user_file_exe:
    return:str-> whether the file is executable or not
    """
    try:
        if 0== subprocess.call(user_file_exe):
            logging.info(f"EXE:executed {user_file_exe}")
            return f"{user_file_exe} is executable"
        else:
            logging.info(f"EXE:executed {user_file_exe} failed")
            return f"{user_file_exe} Failed to execute"
    except Exception as err:
        logging.error(f"EXE:executed {user_file_exe} not found")
        return f"file not found: {err}"


def take_screenshot():
    """
    saves a screenshot of the user to a specific file
    param:None
    return: str->screenshot saved/failed ot save
    """
    try:
        image = pyautogui.screenshot()
        image.save(r'screenshot.jpg')
        logging.info(f"TAKE_SS:Screenshot saved")
        return "image saved"
    except Exception as err:
        logging.error(f"TAKE_SS:Screenshot failed")
        return f"failed to save screenshot: {err}"


def send_screenshot():
    """
    sends the user the screenshot saved in screenshot.jpg
    param:None
    return:
    """
    try:
        with open('screenshot.jpg', 'rb') as screenshot:
            screenshot_bytes = screenshot.read()
            logging.info(f"SEND_SS:Screenshot sent ,bytes saved")
        return screenshot_bytes
    except Exception as err:
        logging.error(f"SEND_SS:Screenshot failed")
        return f"failed to save screenshot: {err}"


def exit_function(client_socket):
    """
    closes the client socket->exits the program for the user
    param client_socket:
    return: None
    """
    try:
        client_socket.close()
        logging.info(f"EXIT:client closed")
    except Exception as err:
        logging.error("failed to close client:" ,{err})


def help_function(data):
    """
    helps the user understand each command
    param data:
    return:str-> containing the help msg of user's desired command
    """
    if data == "DIR":
        logging.info(f"HELP:user requested instruction on DIR")
        return "DIR <path>: lists all files in the specified directory."
    elif data == "REMOVE":
        logging.info(f"HELP:user requested instruction on REMOVE")
        return "REMOVE <file_path.<extension>>: deletes the specified file."
    elif data == "COPY":
        logging.info(f"HELP:user requested instruction on COPY")
        return "COPY <source_path>.<extension> <destination_path>.<extension>: copies a file from source to destination."
    elif data == "EXECUTE":
        logging.info(f"HELP:user requested instruction on EXECUTE")
        return "EXECUTE <file_path>.<executble-extension>: runs the specified script."
    elif data == "SCREENSHOT":
        logging.info(f"HELP:user requested instruction on SCREENSHOT")
        return "SCREENSHOT: takes a screenshot and sends it to client."
    elif data == "EXIT":
        logging.info(f"HELP:user requested instruction on EXIT")
        return "EXIT: closes the connection to the server."
    elif data == "HELP":
        logging.info(f"HELP:user requested instruction on HELP")
        return "HELP <command>: shows usage information for the given command."
    else:
        logging.warning(f"HELP:user requested instruction were not recognized")
        return f"no help available try HELP + <DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT>"


def assert_func():
    """
    checks if all static funcs work
    param:None
    return:None
    """
    check = dir_path(".")
    assert isinstance(check, list)
    assert all(isinstance(x, str) for x in check)
    chgck = remove_file("no_true_file.txt")
    assert isinstance(chgck, str)
    check = copy_files("src.txt", "dest.txt")
    assert isinstance(check, str)
    check = execute_files("non_existing_executable.txt")
    assert isinstance(check, str)
    check = take_screenshot()
    assert isinstance(check, str)
    check = send_screenshot()
    assert isinstance(check, (bytes, str))
    logging.info("all asserts passed")


def main():
    """

    receives a request from user after he connected to the server and answers accordingly
    """
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.bind((SERVER_IP, SERVER_PORT))
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
                        Protocol.send_message(client_socket, cmd,response_to_user)
                        logging.info(f"DIR sent to user")
                    elif cmd == "REMOVE":
                        response_to_user = remove_file(data)
                        Protocol.send_message(client_socket,  cmd,response_to_user)
                        logging.info(f"REMOVE sent to user")
                    elif cmd == "COPY":
                        src, dest = data.split(" ",1)
                        response_to_user = copy_files(src, dest)
                        Protocol.send_message(client_socket, cmd,response_to_user)
                        logging.info(f"COPY sent to user")
                    elif cmd == "EXECUTE":
                        response_to_user = execute_files(data)
                        Protocol.send_message(client_socket, cmd,response_to_user)
                        logging.info(f"EXECUTE sent to user")
                    elif cmd == "SCREENSHOT":
                        take_screenshot()
                        response_to_user = send_screenshot()
                        Protocol.send_message(client_socket,cmd,response_to_user)
                        logging.info(f"SCREENSHOT sent to user")
                    elif cmd == "EXIT":
                        exit_function(client_socket)
                        logging.info('client has exited')
                        break

                    elif cmd == "HELP":
                        response_to_user = help_function(data)
                        Protocol.send_message(client_socket,cmd, response_to_user)
                        logging.info(f"HELP sent to user+<cmd> instruction")
                    else:
                        response_to_user ="invalid command, please try again(DIR/REMOVE/COPY/EXECUTE/SCREENSHOT/EXIT)"
                        Protocol.send_message(client_socket, cmd, response_to_user)
                        logging.warning(f"user sent invalid command")
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
    assert_func()
    main()