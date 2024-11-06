import socket
import subprocess
import ast
import sys
import signal
import os
import hashlib

def start_listener():
    host = '0.0.0.0'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f'Listening on {host}:{port}')
        try:
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f'Connected by {addr}')
                    data_length = int.from_bytes(conn.recv(4), 'big')
                    data = b''
                    while len(data) < data_length:
                        packet = conn.recv(data_length - len(data))
                        if not packet:
                            break
                        data += packet
                    message = ast.literal_eval(data.decode())
                    if message['command'] == 'sync_file':
                        dest_path = message['dest_path']
                        file_data = bytes.fromhex(message['file_data'])
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        with open(dest_path, 'wb') as f:
                            f.write(file_data)
                        print(f'Synced file to {dest_path}')
                    elif message['command'] == 'get_checksums':
                        folder = message['folder']
                        print(f'Calculating checksums for folder: {folder}')
                        checksums = calculate_folder_checksums(folder)
                        print(f'Sending checksums')
                        
                        response = str(checksums).encode('utf-8')
                        response_length = len(response)
                        conn.sendall(response_length.to_bytes(4, 'big'))
                        conn.sendall(response)
                        print('Checksums sent successfully')
                    else:
                        print(f'Unknown command: {message["command"]}')
        except KeyboardInterrupt:
            print('Listener interrupted by user')
            sys.exit(0)
        except Exception as e:
            print(f'Error: {e}')
            sys.exit(1)

def calculate_checksum(file_path):
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        print(f'Error calculating checksum for {file_path}: {e}')
        return None

def calculate_folder_checksums(folder):
    checksums = {}
    try:
        print(f'Starting checksum calculation in folder: {folder}')
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder)
                checksum = calculate_checksum(file_path)
                if checksum:
                    checksums[relative_path] = checksum
                    print(f'File: {relative_path}, Checksum: {checksum}')
    except Exception as e:
        print(f'Error calculating folder checksums: {e}')
    return checksums

if __name__ == '__main__':
    # Handle SIGINT (Ctrl-C)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    start_listener()

