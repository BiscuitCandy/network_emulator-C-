## Vivek Vardhan Reddy Yannam -- VY22
## Kalayandeep Pidikiti -- KP22Y

import socket
import select
import os
import time
import signal
import sys

_lan_name = ""

def sigint_handler(signum, frame):

    print(f"Bridge {lan_name} disconnected")
    for port in bridge.active_ports:
            # if port != source_port:
                # Forward the data frame
            port.send(f"[e]~{lan_name}".encode('utf-8'))
            port.close()
    bridge.server_socket.close()
    sys.exit(0)

class Bridge:

    def __init__(self, lan_name, num_ports):
        while self.check_lan_name(lan_name) :
            print("the lan_name is already in use, try using another name")
            lan_name = input("Plase enter new lan name: ")
        self.lan_name = lan_name
        self.num_ports = num_ports
        self.mac_address_mapping = {}  # To store MAC address to port mapping
        self.active_ports = set()  # To track active ports
        self.setup_socket()
        _lan_name = self.lan_name

    def check_lan_name(self, lan_name):
        return f'{lan_name}.addr' in os.listdir()

    def setup_socket(self):
        # Create a TCP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to a specific IP and port
        # self.server_socket.bind(('127.0.0.1', 0))

        # Get the actual IP address and port number
        self.ip_address = socket.gethostbyname(socket.gethostname())

        # Name the bridge same as it's ip_address
        self.server_socket.bind((self.ip_address, 0))

        self.port = self.server_socket.getsockname()[1]

        print(f"Initiated bridge {self.lan_name} .....")

        # Create symbolic link files for IP address and port number
        os.symlink(str(self.ip_address), f'{self.lan_name}.addr')
        os.symlink(str(self.port), f'{self.lan_name}.port')

        # Listen for incoming connections
        self.server_socket.listen(self.num_ports)

    def handle_connections(self):
        inputs = [sys.stdin, self.server_socket]
        while True:
            # print("*****", self.active_ports)

            readable, _, _ = select.select(inputs + [i for i in self.active_ports], [], [])

            for sock in readable:

                ###
                ## DEALS WITH NEW CONNECTIONS
                ###

                if sock == self.server_socket:
                    # Accept new connections
                    client_socket, addr = self.server_socket.accept()
                    # inputs.append(client_socket)

                    if len(self.active_ports) < self.num_ports:
                        self.handle_new_connection(client_socket)
                    else:
                        # Reject the connection if all ports are in use
                        client_socket.send("reject".encode())
                        print("client", client_socket, "is rejected")
                        client_socket.close()

                ###
                ## DEALS WITH USER INPUT
                ###
                elif sock == sys.stdin:

                    command = sys.stdin.readline()
                    if command.strip() == "[e]" :
                        print("Bridge is Disconneted")
                        for i in self.active_ports :
                            i.send(f"[e]~{self.lan_name}".encode("utf-8"))
                        sys.exit(0)

                    elif command.strip() == "show sl" :
                        if self.mac_address_mapping == {} :
                            print("The self learning table is empty")
                            print("Please try after sometime")

                        print("MAC".center(20), "|", "PORT")
                        # print(self.mac_address_mapping)
                        for i in self.mac_address_mapping:
                            print(i.center(20), "|", self.mac_address_mapping[i][0])

                    elif command.strip() == "[h]" :
                        print("The is the stimulation of Network device called BRIDGE")
                        print("Usage: python bridge.py lan-name num-ports")
                        print("Commands:")
                        print("\t[e] -- exit")
                        print("\t[h] -- help/description")
                        print("\tshow sl -- show the self-learning table")

                    else :
                        print("Improper Command")
                        print("Commands:")
                        print("\t[e] -- exit")
                        print("\t[h] -- help/description")
                        print("\tshow sl -- show the self-learning table")

                ###
                ## DEALS WITH RECIVED DATA_FRAME
                ###
                else :
                    # Handle data frame from an active port
                    data = sock.recv(1024)
                    # print(data.decode("utf-8"))
                    if not data:
                        sock.close()
                        self.active_ports.remove(sock)

                    # try:
                    #     self.handle_data_frame(sock, data.decode('utf-8').strip())
                    # except Exception as e :
                    #     print(e)

                    self.handle_data_frame(sock, data.decode('utf-8').strip())
        self.check_mac_timeout()

    def check_mac_timeout(self) :
        for i in self.mac_address_mapping :
            if time.time() - self.mac_address_mapping[i][1] > 60 :
                self.mac_address_mapping[i] = ()
        
        self.mac_address_mapping = {i: self.mac_address_mapping[i] for i in self.mac_address_mapping if self.mac_address_mapping[i]}

    def handle_new_connection(self, client_socket):
        # Accept the connection
        client_socket.send("accept".encode())
        # stn = client_socket.recv(1024).decode('utf-8').strip()
        print("connected at", client_socket)

        # Add the new connection to the list of active ports
        self.active_ports.add(client_socket)

    def handle_data_frame(self, source_port, data_frame):
        # Check if MAC address mapping exists
        if data_frame.strip() == "":
            return
        # print(data_frame.strip())
        src_mac, dest_mac, src_ip, dest_ip, message = data_frame.split("~", 5)

        if message == "[e]" :
            source_port.close()
            print("Station", "Disconnected")
            self.active_ports.remove(source_port)
            return

        elif message == "[E]" :
            source_port.close()
            print("Router", "Disconnected at")
            self.active_ports.remove(source_port)
            return 

        self.mac_address_mapping[src_mac] = (source_port, time.time())

        if dest_mac not in self.mac_address_mapping:

            # print(message)
            # print(self.mac_address_mapping)

            # Broadcast the data frame to all other ports
            for port in self.active_ports:
                # print("************************************\n", port)
                if port != source_port:
                    # Forward the data frame
                    # print("###########################################")
                    # print(port)
                    # print("###########################################")
                    port.send(data_frame.encode('utf-8'))
                    # print("|||||||||||||||||||||||||||||||||||||||||||")
                    # print("     ARP REQUEST SENT TO OTHER PORTS")
                    # print("|||||||||||||||||||||||||||||||||||||||||||")

            # print("***********************************")

        else :
            # print(message)
            port = self.mac_address_mapping[dest_mac][0]
            port.send(data_frame.encode('utf-8'))

    
    def run(self):
        signal.signal(signal.SIGINT, sigint_handler)
        self.handle_connections()

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python bridge.py lan-name num-ports")
        sys.exit(1)

    lan_name = sys.argv[1]
    num_ports = int(sys.argv[2])

    bridge = Bridge(lan_name, num_ports)

    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, sigint_handler)

    bridge.run()
