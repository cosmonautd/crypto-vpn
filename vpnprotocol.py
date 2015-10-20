import socket
import threading
from Crypto.PublicKey import RSA
import random
import vpncrypto
import os
import sys
import time

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
        self.exchangeKeys()
        try:
            self.read_thread = threading.Thread(target=self.read_encrypted_loop, args=())
            self.read_thread.start()
        except (KeyboardInterrupt, SystemExit):
            sys.exit()

    def connected(self):
        return self.is_connected

    def read(self):
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
        print("Authenticading connection...")
        """
        """
        if self.mode == MODE_SERVER:
            SPuK = self.publickey.exportKey()
            rs1 = bytes(os.urandom(4))
            print("Generated random string:", rs1, "Length:", len(rs1))
            print("Sending public key + rs1...")
            print(SPuK.decode())
            self.write(rs1)
            print("Public key + rs1 sent!")

            print("Waiting for client's public key...")
            message = self.read()
            rs2 = message[:4]
            CPuK = message[4:]
            print("Received random string:", rs2, "Length:", len(rs2))
            print("Received client's public key!")
            print(CPuK.decode())

            serversign = vpncrypto.sha256(rs2+(self.sharedsecret).encode())
            print("Generated signature:", serversign, "Length:", len(serversign))
            self.write(serversign)

            clientsign = self.read()
            print("Received signature:", clientsign, "Length:", len(clientsign))

            self.clientpublickey = RSA.importKey(CPuK)
            if clientsign == vpncrypto.sha256(rs1+self.sharedsecret.encode()):
                print("Client authenticated!")
            else:
                print("Client not authenticated!")
                self.finish()
            print(vpncrypto.sha256(rs1+self.sharedsecret.encode()))

        elif self.mode == MODE_CLIENT:
            CPuK = self.publickey.exportKey()
            print("Waiting for server's public key...")
            message = self.read()
            rs1 = message
            print("Received server's public key!")
            print("Received random string:", rs1, "Length:", len(rs1))

            rs2 = bytes(os.urandom(4))
            print("Generated random string:", rs2, "Length:", len(rs2))
            print("Sending public key...")
            print(CPuK.decode())
            self.write(rs2+CPuK)
            print("Public key sent!")

            serversign = self.read()

            print("Received signature:", serversign, "Length:", len(serversign))

            clientsign = vpncrypto.sha256(rs1+(self.sharedsecret).encode())
            print("Generated signature:", clientsign, "Length:", len(clientsign))
            self.write(clientsign)

            if serversign == vpncrypto.sha256(rs2+self.sharedsecret.encode()):
                print("Server authenticated!")
            else:
                print("Server not authenticated!")
                self.finish()
            print(vpncrypto.sha256(rs2+self.sharedsecret.encode()))

    def exchangeKeys(self):
        print ("\nExchanging AES keys...")
        if self.mode == MODE_SERVER:
            print ("Generating AES key")
            self.AESKey = bytes(os.urandom(16))
            print ("AESkey Generated, AES")

            AESObject = vpncrypto.AESCipher(self.AESKey)
            print ("AES obeject created")

            AESCipher = self.clientpublickey.encrypt(self.AESKey+vpncrypto.sha256(self.AESKey+self.sharedsecret.encode()), 0.0)[0]
            print ("AES key Encrypted")

            print ("Sending Encrypted AES key.")
            self.write(AESCipher)
            print ("Encrypted AES key sent")

            print("Waiting for ACK")
            ACK = self.read()
            print ("ACK received.")

            print ("Decrypting ACK")
            decry = AESObject.decrypt(ACK)  #TODO: Change variable name
            rs3 = decry[:4]
            shaRs = decry[4:]

            if(vpncrypto.sha256(rs3) == shaRs):
                print ("AES key sent with success!")
                self.AESObject = AESObject
            else:
                print ("Error sending AESKey! Closing connection!")
                self.finish()

        elif self.mode == MODE_CLIENT:

            print ("Receiving AES key from the server")
            rawData = self.read()
            print ("AES key from the server Received.")

            print ("Checking AES key integrity")
            decryption = self.keypair.decrypt(rawData)
            self.AESKey = decryption[:16]
            cipherShaAESKey = decryption[16:]

            if (vpncrypto.sha256(self.AESKey+self.sharedsecret.encode()) == cipherShaAESKey):
                print ("AES key authenticated and aquired")
                self.AESObject = vpncrypto.AESCipher(self.AESKey)
                print ("AES obeject created")
            else:
                print ("Integrity check failed, closing connection!")
                self.finish()

            print("Generating ACK for received AES key")
            rs3 = bytes(os.urandom(4))
            ACK = self.AESObject.encrypt(rs3+vpncrypto.sha256(rs3))
            self.write(ACK)
            print ("ACK sent to the server")

    def read_encrypted(self):
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
        aux = self.received_buffer
        self.received_buffer = []
        return aux

    def get_server_ip(self):
        return self.server

    def get_port(self):
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
