import socket
import random
import re

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 3003))
server_socket.listen()

print("Server is running on localhost:3003")

while True:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")

    request = client_socket.recv(1024).decode()
    if not request or 'favicon.ico' in request:
        client_socket.close()
        continue

    request_line = request.splitlines()[0]
    http_method = request_line.split()[0]
    path_and_query = request_line.split()[1]
    path, query = re.match(r'^([^?]*)\?(.*)$', path_and_query).groups()
    pairs = query.split("&")

    params = {}

    for param in pairs:
        key, value = param.split("=")
        params[key] = value

    rolls_str = ""

    for times in range(int(params['rolls'])):
        roll = random.randint(1, int(params['sides']))
        rolls_str += f"Roll: {roll}\n"


    roll = random.randint(1, 6)
    response_body = (f"Request Line: {request_line}\n"
                    f"HTTP Method: {http_method}\n"
                    f"Path: {path} \n"
                    f"Parameters: {params}\n"
                    f"{rolls_str}"    
                    )
    
    response = ("HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "\r\n"
                f"{response_body}\n")
 

    client_socket.sendall(response.encode())
    client_socket.close()