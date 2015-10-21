import socket
import threading
from Crypto.PublicKey import RSA
import random
import vpncrypto
import os
import sys
import time
import binascii

MODE_SERVER = 0
MODE_CLIENT = 1

class Connection:

    def __init__(self, server, port, ss, mode=MODE_SERVER, printmode=False):
        self.server = server
        self.port = port
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if mode == MODE_SERVER or mode == MODE_CLIENT:
            self.mode = mode
        else: raise ValueError("Invalid connection mode. \
                Should be Connection.MODE_SERVER or Connection.MODE_CLIENT")
        if self.mode == MODE_SERVER:
            self.client = None
            self.client_addr = None
            self.clientpublickey = None
        elif self.mode == MODE_CLIENT:
            self.serverpublickey = None
        self.AESKey = None
        self.is_connected = False
        self.read_thread = None
        self.printmode = printmode;
        self.sharedsecret = ss
        self.keypair = RSA.generate(2048)
        self.publickey = self.keypair.publickey()
        self.AESObject = None
        self.received_buffer = []

    def start(self):
        """
            Start socket connection, authenticate server and client and exchange
            keys between server and client
        """
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
        print("Starting key exchange protocol")
        self.exchangeKeys()
        try:
            self.read_thread = threading.Thread(target=self.read_encrypted_loop, args=())
            self.read_thread.start()
        except (KeyboardInterrupt, SystemExit):
            sys.exit()

    def connected(self):
        return self.is_connected

    def read(self):
        """
            Reads data thgough the socket
        """
        if self.connected():
            data = ""
            if self.mode == MODE_SERVER:
                data = self.client.recv(1024)
            elif self.mode == MODE_CLIENT:
                data = self.socket.recv(1024)
            try:
                if data.decode() == "f#":
                    self.finish()
            except UnicodeDecodeError:
                pass
            return data

    def write(self, data):
        """
        Sends data through the socket
        """
        if self.connected():
            if self.mode == MODE_SERVER:
                self.client.send(data)
            elif self.mode == MODE_CLIENT:
                self.socket.send(data)
        try:
            if data.decode() == "f#":
                self.finish()
        except UnicodeDecodeError:
            pass

    def auth(self):
        print("Authenticating connection...")
        """
        """
        if self.mode == MODE_SERVER:
            SPuK = self.publickey.exportKey()
            #TODO: Generate b

            print("Waiting for nonce rs1 and client's public key...")
            message = self.read()
            rs1 = message[:4]
            CPuK = message[4:]
            print("Received nonce rs1:", binascii.hexlify(rs1).decode().upper(), "Length:", len(rs2))
            print("Received client's public key!")
            print(CPuK.decode())

            self.clientpublickey = RSA.importKey(CPuK)

            rs2 = bytes(os.urandom(4))
            print("Generated nonce rs2:", binascii.hexlify(rs1).decode().upper(), "Length:", len(rs2))

            challenge1 = rs2+self.clientpublickey.encrypt(vpncrypto.sha256(rs1+self.sharedsecret.encode()+g^b mod p), 0.0)[0] #TODO: chage 'g^b mod p' for real values
            print("Sending Server Public key...")
            self.write(SPuK)
            print("Sending challenge1 = rs2+E(CPuK,sha(rs1||sharedsecret)+g^b mod p)...")
            self.write(challenge1)

            print("Waiting for client's response E(SPuK,sha(rs2||sharedsecret)+g^a mod p)...")
            challenge2 = self.read()

            integrity = challenge1[:***] #TODO: change *** for len(sha(rs1+ss))
            half_key = challenge1[***:]

            if integrity == vpncrypto.sha256(rs2+self.sharedsecret.encode()):
                print("Client authenticated!")
            else:
                print("Client not authenticated!")
                self.finish()

            #TODO: calculate full_key = 'g^a*b mod p' = (half_key^b)
            #TODO: destroy b

            print ("AES key aquired")
            self.AESObject = vpncrypto.AESCipher(full_key)
            print ("AES obeject created")

        elif self.mode == MODE_CLIENT:
            CPuK = self.publickey.exportKey()

            #TODO: Generate a

            rs1 = bytes(os.urandom(4))
            print("Generated nonce rs1:", binascii.hexlify(rs1).decode().upper(), "Length:", len(rs1))
            print("Sending public key and nonce rs1...")
            self.write(rs1+CPuK)
            print("Public key sent!")
            print(CPuK.decode())

            print("Waiting for server's public key...")
            SPuK = self.read()
            self.serverpublickey = RSA.importKey(SPuK)


            print("Waiting for server's response rs2+E(CPuK,sha(rs1||sharedsecret)+g^b mod p)...")
            challenge1 = self.read()

            rs2 = challenge1[:4]
            integrity = challenge1[4:***] #TODO: change *** for len(sha(rs1+ss)+4)
            half_key = challenge1[***:]

            if integrity == vpncrypto.sha256(rs1+self.sharedsecret.encode()):
                print("Server authenticated!")
            else:
                print("Server not authenticated!")
                self.finish()

            challenge2 = self.serverpublickey.encrypt(vpncrypto.sha256(rs2+self.sharedsecret.encode()+g^a mod p), 0.0)[0] #TODO: chage 'g^a mod p' for real values

            #TODO: calculate full_key = 'g^b*a mod p' = (half_key^a)
            #TODO: destroy a

            print ("AES key aquired")
            self.AESObject = vpncrypto.AESCipher(full_key)
            print ("AES obeject created")

    def read_encrypted(self):
        """
            Reads received encrypted data and than decrypts using the AES key
        """
        encrypted_data = []
        if self.AESObject:
            if self.connected():
                data = ""
                try:
                    if self.mode == MODE_SERVER:
                        encrypted_data = self.client.recv(1024)
                    elif self.mode == MODE_CLIENT:
                        encrypted_data = self.socket.recv(1024)
                except socket.error:
                    pass

                if len(encrypted_data) > 0:
                    data = self.AESObject.decrypt(encrypted_data)
                    sha = data[:32]
                    data = data[32:]
                    if not vpncrypto.sha256(data) == sha:
                        print("Received message could not be verified! Integrity problems.")
                        self.finish()
                else: data = "".encode()

                try:
                    if data.decode() == "f#":
                        self.finish()
                except UnicodeDecodeError:
                    pass
                return data

    def write_encrypted(self, data):
        """
            Sends encrypted data through the socket
        """
        if self.AESObject:
            if self.connected():
                data = vpncrypto.sha256(data) + data
                encrypted_data = self.AESObject.encrypt(data)
                if self.mode == MODE_SERVER:
                    self.client.send(encrypted_data)
                elif self.mode == MODE_CLIENT:
                    self.socket.send(encrypted_data)
                time.sleep(0.1)

    def read_encrypted_loop(self):
        """
            Function called by a thread that keep listening for new messages\
            until the connection is closed
        """
        message = ""
        while self.connected():
            message = (self.read_encrypted()).decode()
            self.received_buffer.append(message)
            if self.printmode:
                if self.mode == MODE_SERVER:
                    print(self.client_addr, message, "\n>> ", end="")
                elif self.mode == MODE_CLIENT:
                    print("(" + self.server + ")", message, "\n>> ", end="")
        #self.finish()

    def get_received_buffer(self):
        """
            Get the buffer of received messages and than clean the buffer
        """
        aux = self.received_buffer
        self.received_buffer = []
        return aux

    def get_server_ip(self):
        """
            Returns the server IP
        """
        return self.server

    def get_port(self):
        """
            Returns the port used in the communication
        """
        return self.port

    def finish(self):
        print("Finishing connection...")
        print("Closing all sockets...")
        if self.mode == MODE_SERVER:
            self.client.close()
        self.socket.close()
        self.is_connected = False
        print("All sockets closed!")
        print("Connection finished!")
