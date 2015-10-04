import vpnprotocol

connection = None

print("Do you want to be a (s)erver or a (c)lient?")
choice = input(">> ")

if choice == "s": connection = vpnprotocol.Connection("localhost", 7890, printmode=True)
elif choice == "c": connection = vpnprotocol.Connection("localhost", 7890, vpnprotocol.MODE_CLIENT, printmode=True)
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

"""while connection.connected():
    command = input(">> ")
    connection.write(command.encode())
connection.finish()"""
