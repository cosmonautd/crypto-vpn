import vpnprotocol

connection = None

print("Do you want to be a (s)erver or a (c)lient?")
choice = input(">> ")

print("Input shared secret:")
ss = input(">> ")

if choice == "s": connection = vpnprotocol.Connection("localhost", 7890, ss, printmode=True)
elif choice == "c": connection = vpnprotocol.Connection("localhost", 7890, ss, vpnprotocol.MODE_CLIENT, printmode=True)
else:
    print("You rebel!")
    quit()

print("Type s to start connection!")
command = input(">> ")

if command == "s":
    connection.start()
    print("Type f# to finish connection!")
else:
    print("Sorry!")
    quit()

while connection.connected():
    command = input(">> ")
    connection.write_encrypted(command.encode())
connection.finish()
