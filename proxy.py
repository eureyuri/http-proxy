from socket import *
from re import *
import select
import sys
import os
from datetime import datetime

BUFF_SIZE = 1024
LISTEN_PORT = 8080  # Default value
HOST_NAME = "localhost"
SERVER_PORT = 80  # Server socket address


# Send GET request to server socket
def sendToServer(serverSocket, path):
    get_request = str.encode("GET " + path + " HTTP/1.0\r\n\r\n")
    serverSocket.send(get_request)
    # print(get_request)


# Receive message from socket
# Returns a tuple (body, response header, is_redirect)
def receiveFromServer(serverSocket):
    is_redirect = False

    # Retrieve all response
    response_all = b""
    while True:
        response = serverSocket.recv(BUFF_SIZE)
        response_all += response
        if not response:
            break

    # Extract responseLine and body
    response_list = response_all.split(b"\r\n\r\n")
    responseLine = response_list[0] + b"\r\n\r\n"
    body = response_list[1]

    if checkStatusCode(responseLine, "301"):
        # Handle 301
        body, responseLine, is_redirect = handle301(responseLine, is_redirect)
    elif checkStatusCode(responseLine, "404"):
        # Handle 404
        responseLine = b"HTTP/1.0 404 Not Found\r\n\r\n"
        body = b"<html><body><center><h1>Error 404: File not found</h1></center></body></html>"

    return body, responseLine, is_redirect


# Checks if the response matches the specified status code
def checkStatusCode(responseLine, status_code):
    return responseLine.decode().split(" ")[1] == status_code


# Handles 301 response
def handle301(responseLine, is_redirect):
    # Parsing to get the new location for the redirect
    for s in responseLine.decode().split("\r\n\r\n")[0].split("\r\n"):
        if s.startswith("Location"):
            location = s.split(" ")[1]

    url = location.split("/")
    domain = url[2]
    loc_length = len(url[0]) + len("//") + len(url[1]) + len(domain)
    location = location[loc_length:]

    # New socket to get the redirected location
    serverSocketRedirect = connectSocket(domain, SERVER_PORT)
    sendToServer(serverSocketRedirect, location)
    body, responseLine, is_redirect = receiveFromServer(serverSocketRedirect)
    is_redirect = True

    return body, responseLine, is_redirect


# Create socket to listen on
def createProxySocket(listen_port):
    proxySocket = socket(AF_INET, SOCK_STREAM)
    proxySocket.bind((HOST_NAME, listen_port))
    proxySocket.listen(5)
    return proxySocket


def connectSocket(domain, serverPort):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.connect((domain, serverPort))
    return serverSocket


# Checks cache for file
# appends index.html to a request for a directory
# returns the body and response code from the server
def checkCache(current_dir, request, domain):
    filename = current_dir + request
    path = request[len(domain):][1:]

    # Append index.html for a request to directory
    if (filename[-1] == '/'):
        filename += "index.html"
        path += "index.html"

    # Check if the request exists in cache
    if os.path.exists(filename):
        # If the the path exists but is not a file, check if it is a
        # redirect response. If it is, we already have the cache so retrieve it
        if not os.path.isfile(filename):
            checkSocket = connectSocket(domain, SERVER_PORT)
            sendToServer(checkSocket, path)
            body, responseLine, is_redirect = receiveFromServer(checkSocket)
            if is_redirect:
                filename += "/index.html"
        with open(filename, "rb") as f:
            print("###################")
            print("Reading from cache")
            print("###################")
            # Remove timestamp from file
            f.readline()
            body = f.read()
            responseLine = b"HTTP/1.0 200 OK\r\n\r\n"
    else:
        # First visit: No cache
        serverSocket = connectSocket(domain, SERVER_PORT)
        print("Server connected")

        sendToServer(serverSocket, path)
        print("Sent to server")

        body, responseLine, is_redirect = receiveFromServer(serverSocket)

        # Images may exist in a different directory structure
        if checkStatusCode(responseLine, "404"):
            checkSocket = connectSocket(domain, SERVER_PORT)

            # Reconstruct correct path
            new_path = ""
            path_list = path.split("/")
            add = False
            for i in range(len(path_list)):
                if add:
                    new_path += "www.hats.com/"
                if "test" in path_list[i]:
                    add = True
                new_path += path_list[i] + "/"

            sendToServer(checkSocket, new_path[:-1])
            body, responseLine, is_redirect = receiveFromServer(checkSocket)

        # Try to cache only if the response is not 404
        if not checkStatusCode(responseLine, "404"):
            try:
                if (is_redirect):
                    filename += "/index.html"
                os.makedirs(os.path.dirname(filename))
            except Exception:
                # Directory has already been made so just write file
                pass

            # Write cache with timestamp
            with open(filename, "wb") as f:
                f.write((datetime.now().strftime(
                    "%d-%b-%Y (%H:%M:%S.%f)") + "\n").encode())
                f.write(body)

    return body, responseLine


def main():
    # Get port for client
    try:
        LISTEN_PORT = int(sys.argv[1])
    except Exception:
        print("Please enter an int")
        sys.exit(2)

    # Create proxy socket
    proxySocket = createProxySocket(LISTEN_PORT)

    while True:
        # Accept a connection
        clientSocket, clientAddr = proxySocket.accept()
        print("Client socket accepted")

        readable, _, _ = select.select([clientSocket], [], [], 0.1)

        if readable:
            raw_message = clientSocket.recv(BUFF_SIZE)
            clientMessage = raw_message.decode(errors='ignore')
            # print("\nClient message \n****\n" + clientMessage + "\n****\n")

            # Parse requests
            # first line is "GET /path HTTP/1.0\r\n" so we want /path/
            request = clientMessage.split(" ")[1]
            domain = request.split("/")[1]

            if domain == "favicon.ico" or domain == "node":
                # Just ignore the favicon and node
                continue
            else:
                sysPath = os.getcwd()
                body, responseLine = checkCache(sysPath, request, domain)
                clientSocket.send(responseLine)
                clientSocket.send(body)
                print("###################")
                print("RESPONSE LINE : " + responseLine.decode().split(" ")[1])
                print("###################")
                print("Server received")

            clientSocket.close()  # close socket to wait for new request
        else:
            print("Closing")
            clientSocket.close()

    proxySocket.close()


if __name__ == "__main__":
    main()
