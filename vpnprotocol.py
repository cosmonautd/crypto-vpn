import socket
import threading
from Crypto.PublicKey import RSA

MODE_SERVER = 0
MODE_CLIENT = 1

class Connection:

    def __init__(self, server, port, mode=MODE_SERVER, printmode=False):
        self.server = server
        self.port = port
        self.socket = socket.socket()
        if mode == MODE_SERVER or mode == MODE_CLIENT:
            self.mode = mode
        else: raise ValueError("Invalid connection mode. \
                Should be Connection.MODE_SERVER or Connection.MODE_CLIENT")
        if self.mode == MODE_SERVER:
            self.client = None
            self.client_addr = None
        self.is_connected = False
        self.read_thread = None
        self.printmode = printmode;
        self.keypair = RSA.generate(2048)
        self.publickey = self.keypair.publickey()

    def start(self):
        print("Starting connection...")
        if self.mode == MODE_SERVER:
            print("Binding server address and port...")
            self.socket.bind((self.server, self.port))
            self.socket.listen(1)
            print("Server on and listening...")
            (self.client, self.client_addr) = self.socket.accept()
            self.is_connected = True
            print("Incoming connection accepted!")
            print("Client address is", self.client_addr)
        elif self.mode == MODE_CLIENT:
            print("Connecting with server at", self.server, "port", self.port)
            self.socket.connect((self.server, self.port))
            self.is_connected = True
            print("Connection accepted!")
        print("Starting authentication protocol!")
        self.auth()
        #self.read_thread = threading.Thread(target=self.read_loop, args=())
        #self.read_thread.start()

    def connected(self):
        return self.is_connected

    def read(self):
        if self.connected():
            data = ""
            if self.mode == MODE_SERVER:
                data = self.client.recv(1024)
            elif self.mode == MODE_CLIENT:
                data = self.socket.recv(1024)
            return data

    def read_loop(self):
        message = ""
        while not message == "f#" and self.connected():
            message = (self.read()).decode()
            if self.printmode:
                if self.mode == MODE_SERVER:
                    print(self.client_addr, message, "\n>> ", end="")
                elif self.mode == MODE_CLIENT:
                    print("(" + self.server + ")", message, "\n>> ", end="")
        self.finish()

    def write(self, data):
        if self.connected():
            if self.mode == MODE_SERVER:
                self.client.send(data)
            elif self.mode == MODE_CLIENT:
                self.socket.send(data)
        if data.decode() == "f#":
            self.finish()

    def auth(self):
        """
        """
        if self.mode == MODE_SERVER:
            SPuK = self.publickey.exportKey()
            print("Sending public key...")
            print(SPuK.decode())
            self.write(SPuK)
            print("Public key sent!")
            print("Waiting for client's public key...")
            CPuK = self.read()
            print("Received client's public key!")
            print(CPuK.decode())
        elif self.mode == MODE_CLIENT:
            CPuK = self.publickey.exportKey()
            print("Waiting for server's public key...")
            SPuK = self.read()
            print("Received server's public key!")
            print(SPuK.decode())
            print("Sending public key...")
            print(CPuK.decode())
            self.write(CPuK)
            print("Public key sent!")

    def finish(self):
        if self.connected():
            print("Finishing connection...")
            print("Closing all sockets...")
            if self.mode == MODE_SERVER:
                self.client.close()
            self.socket.close()
            self.is_connected = False
            print("All sockets closed!")
            print("Connection finished!")
