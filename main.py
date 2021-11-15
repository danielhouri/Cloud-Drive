import os
import random
import socket
import string
import sys
import shutil

PKI_DICT = {}


def generate_key():
    result = ""
    pattern = string.digits + string.ascii_lowercase + string.ascii_uppercase
    for i in range(0, 128):
        result = result + random.choice(pattern)
    return result


def get_list(client_socket):
    size = client_socket.recv(15).decode('UTF-8')
    client_socket.send("EOT".encode('UTF-8'))
    data = client_socket.recv(int(size)).decode('UTF-8')
    data = data.split(',')
    return data


def download_file(client_socket, filename, path):
    file = open(path + '/' + filename, 'wb+')
    while True:
        data = client_socket.recv(1024)
        if len(data) >= 3 and data[-3:] == b'FTF':
            file.write(data[:-3])
            break
        file.write(data)
    file.close()


def download_dir(client_socket, path):
    # Download the folder names and create the folders
    data = get_list(client_socket)
    for directory in data:
        new_path = path + '/' + directory
        os.mkdir(new_path)

    # Download the file names and create the files
    data = get_list(client_socket)
    for filename in data:
        client_socket.send("FTS".encode('UTF-8'))
        download_file(client_socket, filename, path)


def new_account(client_socket):
    # Generate and sent a key to the new client
    key = generate_key()
    client_socket.send(key.encode('UTF-8'))

    # Open a folder for the new client - the folder name is the key
    os.mkdir(key)
    download_dir(client_socket, key)


def send_list(data_list, client_socket, path):
    # Send directory names
    data = []
    for name in data_list:
        temp = (name.split(path)[1])[1:]
        data.append(temp)
    data = ','.join(data)

    client_socket.send(str(len(data)).encode('UTF-8'))
    temp = client_socket.recv(15).decode('UTf-8')
    if temp != "EOT":
        return 1
    client_socket.send(data.encode('UTF-8'))


def send_file(filename, client_socket):
    # Send directory names
    file = open(filename, 'rb')
    data = file.read(1024)
    while data:
        client_socket.send(data)
        data = file.read(1024)

    client_socket.send("FTF".encode('UTF-8'))
    file.close()


def upload_dir(file_list, folder_list, client_socket, key):
    send_list(folder_list, client_socket, key)
    send_list(file_list, client_socket, key)

    for filename in file_list:
        temp = client_socket.recv(15).decode('UTf-8')
        if temp == "FTS":
            send_file(filename, client_socket)


def get_file_directory(path):
    all_files = []
    all_directories = []
    walk = [path]
    while walk:
        folder = walk.pop(0) + "/"
        all_directories.append(folder)
        # items = folders + files
        items = os.listdir(folder)
        for i in items:
            i = folder + i
            (walk if os.path.isdir(i) else all_files).append(i)
    return all_files, all_directories[1:]


def existing_account(client_socket):
    client_socket.send("KEY".encode('UTF-8'))
    key = client_socket.recv(1024).decode('UTF-8')
    file_list, folder_list = get_file_directory(key)
    upload_dir(file_list, folder_list, client_socket, key)


def get_request(client_socket, str, str1, getfile):
    client_socket.send("KEY".encode('UTF-8'))
    key = client_socket.recv(1024).decode('UTF-8')
    client_socket.send(str.encode('UTF-8'))
    src = client_socket.recv(1024).decode('UTF-8')
    src_full = key + '/' + src
    dst = ""
    if str1 != "":
        client_socket.send(str1.encode('UTF-8'))
        dst = key + '/' + client_socket.recv(1024).decode('UTF-8')
    if getfile == 1:
        os.remove(src_full)
        download_file(client_socket, src, key)
    return src_full, dst


if __name__ == '__main__':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', int(sys.argv[1])))
    server.listen(5)
    while True:
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        data = client_socket.recv(1024).decode('UTF-8')

        if data == "000":
            new_account(client_socket)
        elif data == "111":
            existing_account(client_socket)
        elif data == "222":
            src, dst = get_request(client_socket, "SFT", "", 0)
            os.mkdir(src)
        elif data == "333":
            src, dst = get_request(client_socket, "NAM", "", 0)
            file = open(src, 'wb')
            file.close()
        elif data == "444":
            src, dst = get_request(client_socket, "NAD", "", 0)
            if os.path.exists(src):
                shutil.rmtree(src)
        elif data == "555":
            src, dst = get_request(client_socket, "NAD", "", 0)
            os.remove(src)
        elif data == "666":
            src, dst = get_request(client_socket, "NAD", "NAD", 0)
            os.rename(src, dst)
        elif data == "777":
            src, dst = get_request(client_socket, "NAD", "", 1)

        client_socket.close()
