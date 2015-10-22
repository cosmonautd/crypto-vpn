import socket
import threading
from Crypto.PublicKey import RSA
import random
import vpncrypto
import os
import sys
import time
import binascii
from struct import Struct

MODE_SERVER = 0
MODE_CLIENT = 1

class Connection:

    def __init__(self, server, port, ss, mode=MODE_SERVER, printmode=False):
        self.unpacker = Struct("B")
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

        self.generator = 2
        self.prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6BF12FFA06D98A0864D87602733EC86A64521F2B18177B200CBBE117577A615D6C770988C0BAD946E208E24FA074E5AB3143DB5BFCE0FD108E4B82D120A92108011A723C12A787E6D788719A10BDBA5B2699C327186AF4E23C1A946834B6150BDA2583E9CA2AD44CE8DBBBC2DB04DE8EF92E8EFC141FBECAA6287C59474E6BC05D99B2964FA090C3A2233BA186515BE7ED1F612970CEE2D7AFB81BDD762170481CD0069127D5B05AA993B4EA988D8FDDC186FFB7DC90A6C08F4DF435C934063199FFFFFFFFFFFFFFFF
        self.key_size = 64
        self.DH_private_key = self.gen_DHPrK(self.key_size)
        self.DH_public_key = self.gen_DHPuK()

    def int2bytes(self, input_int):
        return str(input_int).encode()

    def bytes2int(self, input_bytes):
        return int(input_bytes.decode())


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
        print("Starting authentication/exchange keys protocol!")
        self.auth()

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

    def gen_DHPrK(self, DH_key_size):
        return random.SystemRandom().randint(2**(DH_key_size-1), 2**DH_key_size)
        #return bytes2int(os.urandom(DH_key_size)) #TODO: remove hardcoded "random"

    def gen_DHPuK(self):
        return pow(self.generator,self.DH_private_key,self.prime)

    def gen_AES_key(self,half_key):
        return pow(half_key,self.DH_private_key,self.prime)

    def auth(self):
        print("Authenticating connection...")
        """
        """
        if self.mode == MODE_SERVER:
            SPuK = self.publickey.exportKey()

            print("Waiting for nonce rs1 and client's public key...")
            message = self.read()
            rs1 = message
            print("Received nonce rs1:", binascii.hexlify(rs1).decode().upper(), "Length:", len(rs1))
            print("Received client's public key!")

            temp_aes = vpncrypto.AESCipher(vpncrypto.sha256(rs1+self.sharedsecret.encode()))

            rs2 = bytes(os.urandom(4))
            print("Generated nonce rs2:", binascii.hexlify(rs1).decode().upper(), "Length:", len(rs2))

            challenge1 = rs2+temp_aes.encrypt("server".encode()+rs1+self.int2bytes(self.DH_public_key))

            print("Sending challenge1 = rs2+E(CPuK,sha(rs1||sharedsecret)+g^b mod p)...")
            self.write(challenge1)

            temp_aes2 = vpncrypto.AESCipher(vpncrypto.sha256(rs2+self.sharedsecret.encode()))

            print("Waiting for client's response E(SPuK,sha(rs2||sharedsecret)+g^a mod p)...")
            challenge2 = self.read()

            decrypted = temp_aes1.decrypt(check) #TODO: BYTES PROBLEMS "server" tem que temanho?
            message = decrypted[:6]
            rs2_client = decrypted[6:10]
            DH_client_key = decrypted[10:]

            if (message == "client" and rs2_client == rs2):
                print("Client authenticated!")
            else:
                print("Client not authenticated!")
                self.finish()


            integer = bytes2int(DH_client_key)

            real_aes_key = self.gen_AES_key(integer)
            #                                    /\
            #************************************||************************
            #calculate full_key = 'g^a*b mod p' = (half_key^b)
            full_key = self.gen_AES_key(half_key)
            #destroy b
            self.DH_private_key = 0
            #**************************************************************

            print ("AES key aquired")
            self.AESObject = vpncrypto.AESCipher(full_key)
            print ("AES obeject created")

        elif self.mode == MODE_CLIENT:
            CPuK = self.publickey.exportKey()

            rs1 = bytes(os.urandom(4))
            print("Generated nonce rs1:", binascii.hexlify(rs1).decode().upper(), "Length:", len(rs1))
            print("Sending nonce rs1...")
            self.write(rs1)
            print("Nonce sent!")

            temp_aes1 = vpncrypto.AESCipher(vpncrypto.sha256(rs1+self.sharedsecret.encode()))

            print("Waiting for server's response rs2+E(CPuK,sha(rs1||sharedsecret)+g^b mod p)...")
            challenge1 = self.read()

            rs2 = challenge1[:4]
            check = challenge1[4:]

            decrypted = temp_aes1.decrypt(check) #TODO: BYTES PROBLEMS "server" tem que temanho?
            message = decrypted[:6]
            rs1_server = decrypted[6:10]
            DH_server_key = decrypted[10:]

            if (message == "server" and rs1_server == rs1):
                print("Server authenticated!")
            else:
                print("Server not authenticated!")
                self.finish()

            DH_server_key = self.bytes2int(DH_server_key)

            real_aes_key = self.gen_AES_key(DH_server_key)

            temp_aes2 = vpncrypto.AESCipher(vpncrypto.sha256(rs2+self.sharedsecret.encode()))

            challenge2 = self.temp_aes2.encrypt("client".encode()+rs2+bytes([self.DH_public_key])) #TODO: BYTES PROBLEMS

            #**********************************************************************
            #calculate full_key = 'g^b*a mod p' = (half_key^a)
            full_key = self.gen_AES_key(half_key)
            #destroy a
            self.DH_private_key = 0
            #**********************************************************************

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
