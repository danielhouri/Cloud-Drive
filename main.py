import os
import random
import socket
import string
import sys
import shutil

HISTORY = {}


def make_request(code, src_path, dst_path, getfile, key, sock):
    sock.sendall(code.encode() + b'\n')

    new_path = (src_path.split(key)[1])[1:]
    sock.sendall(str(new_path).encode() + b'\n')

    if dst_path != "":
        new_path = (dst_path.split(key)[1])[1:]
        sock.sendall(str(new_path).encode() + b'\n')

    if getfile == 1:
        send_file(src_path, sock)


def generate_key():
    result = ""
    pattern = string.digits + string.ascii_lowercase + string.ascii_uppercase
    for i in range(0, 128):
        result = result + random.choice(pattern)
    return result


def get_list(cli_file):
    data_list = cli_file.readline().strip().decode()
    data_list = data_list.split(',')
    return data_list


def download_file(filename, path, cli_file):
    size = int(cli_file.readline())
    to_write = cli_file.read(size)
    with open(os.path.join(path, filename), 'wb') as f:
        f.write(to_write)


def send_file(filename, sock):
    # Send directory names
    size = os.path.getsize(filename)
    sock.sendall(str(size).encode() + b'\n')

    with open(filename, 'rb') as f:
        sock.sendall(f.read())


def download_dir(path, cli_file):
    # Download the folder names and create the folders
    data_list = get_list(cli_file)
    for directory in data_list:
        new_path = path + '/' + directory
        os.mkdir(new_path)

    # Download the file names and create the files
    data_list = get_list(cli_file)
    for filename in data_list:
        download_file(filename, path, cli_file)


def new_account(sock, cli_file):
    # Generate and sent a key to the new client
    key = generate_key()
    sock.sendall(key.encode() + b'\n')
    HISTORY[key] = []
    print(key)

    # Open a folder for the new client - the folder name is the key
    os.mkdir(key)
    download_dir(key, cli_file)


def send_list(data_list, sock, path):
    # Send directory names
    res = []
    for name in data_list:
        temp = (name.split(path)[1])[1:]
        res.append(temp)
    res = ','.join(res)

    sock.sendall(res.encode() + b'\n')


def upload_dir(file_list, folder_list, sock, key):
    send_list(folder_list, sock, key)
    send_list(file_list, sock, key)

    for filename in file_list:
        send_file(filename, sock)


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


def existing_account(sock):
    key = client_file.readline().strip().decode()
    file_list, folder_list = get_file_directory(key)
    upload_dir(file_list, folder_list, sock, key)


def get_request(code, cli_file, str1, getfile):
    key = client_file.readline().strip().decode()
    ntu = float(client_file.readline())
    src_name = client_file.readline().strip().decode()
    src_full = key + '/' + src_name

    dst_full = ""
    if str1 != "":
        dst_full = key + '/' + client_file.readline().strip().decode()
    if getfile == 1:
        os.remove(src_full)
        download_file(src_name, key, cli_file)

    # Add the request to the history
    user_history = HISTORY[key]
    op = code + "?" + src_full + "?" + dst_full
    temp = [float(ntu), op]
    user_history.append(temp)
    print(temp)

    return src_full, dst_full


def update_client(sock, cli_file):
    key = cli_file.readline().strip().decode()
    last_update = float(cli_file.readline())
    user_history = HISTORY[key]

    for event in user_history:
        if last_update < float(event[0]):
            comm = event[1].split('?')
            opp = comm[0]
            src_full = comm[1]
            if opp == "222":
                make_request("222", src_full, "", 0, key, sock)
            elif opp == "333":
                make_request("333", src_full, "", 0, key, sock)
            elif opp == "444":
                make_request("444", src_full, "", 0, key, sock)
            elif opp == "555":
                make_request("555", src_full, "", 0, key, sock)
            elif opp == "666":
                dst_full = comm[2]
                make_request("666", src_full, dst_full, 0, key, sock)
            elif opp == "777":
                make_request("777", src_full, "", 1, key, sock)
    sock.sendall("NOU".encode() + b'\n')


if __name__ == '__main__':
    globals()
    HISTORY['123a'] = []

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', int(sys.argv[1])))
    server.listen(5)

    while True:
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        with client_socket, client_socket.makefile('rb') as client_file:

            data = client_file.readline()
            if not data:
                break
            data = data.strip().decode()

            if data == "000":
                # New account - create a new folder on the server and download the content
                new_account(client_socket, client_file)
            elif data == "111":
                # Existing account - create a new folder on the client and download the content
                existing_account(client_socket)
            elif data == "222":
                # 222 - create a new folder
                src, dst = get_request(data, client_file, "", 0)
                os.mkdir(src)
            elif data == "333":
                # 333 - Create a new file
                src, dst = get_request(data, client_file, "", 0)
                file = open(src, 'wb')
                file.close()
            elif data == "444":
                # 444 - Remove a folder
                src, dst = get_request(data, client_file, "", 0)
                if os.path.exists(src):
                    shutil.rmtree(src)
            elif data == "555":
                # 555 - Remove a file
                src, dst = get_request(data, client_file, "", 0)
                os.remove(src)
            elif data == "666":
                # 666 - Rename a file / folder
                src, dst = get_request(data, client_file, "NAD", 0)
                os.rename(src, dst)
            elif data == "777":
                # 777 - Get changes in a file
                src, dst = get_request(data, client_file, "", 1)
            elif data == "888":
                # 888 - Get updates
                update_client(client_socket, client_file)

        client_socket.close()
