# Vivek Vardhan Reddy Yannam -- VY22
# Kalyandeep Pidikiti -- KP22Y


import socket
import threading
import os
import select
import time
import sys
import signal
import fcntl

# def sigint_handler(signum, frame):

#     print("Disconnecting from bridge ... ")
#     msg = "src_mac~dest_mac~src_ip~dest_ip~" + ("[E]" if is_router else "[e]")
#     for s in self.client_socket : 
#         self.client_socket[s].send(msg.encode('utf-8'))
#     for s in self.client_socket :
#         self.client_socket[s].close()
#     sys.exit(0)

class Station:
    def __init__(self, interface_file, routingtable_file, hostname_file, is_router):
        self.arp_cache = {}
        self.pending_packets = []
        self.client_socket = {}
        self.interface_data = self.load_interface(interface_file)
        self.routing_table = self.load_routing_table(routingtable_file)
        self.hostname_mapping = self.load_hostname_mapping(hostname_file)
        self.is_router = is_router
        self.route_ip = {}

        signal.signal(signal.SIGINT, self.sigint_handler)

    def sigint_handler(self, signum, frame):

        print("Disconnecting from bridge ... ")
        msg = "src_mac~dest_mac~src_ip~dest_ip~" + ("[E]" if is_router else "[e]")
        for s in self.client_socket : 
            self.client_socket[s].send(msg.encode('utf-8'))
        for s in self.client_socket :
            self.client_socket[s].close()
        sys.exit(0)

    def load_interface(self, filename):
        # Load interface information from the file and return data structure
        interface_data = {}
        try:
            with open(filename, 'r') as file:
                for line in file.readlines():
                    # print("ILINE", line)
                    tokens = line.strip().split()
                    if len(tokens) == 5:
                        interface_name, ip_address, subnet_mask, mac_address, lan_name = tokens
                        interface_data[interface_name] = {
                            'ip_address': ip_address,
                            'subnet_mask': subnet_mask,
                            'mac_address': mac_address,
                            'lan_name': lan_name
                        }
                        self.arp_cache[ip_address] = (mac_address, -1)
                    else:
                        print(f"Skipping invalid line in {filename}: {line}")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error: {filename} not found.") from e
            exit(0)
        except Exception as e:
            raise RuntimeError(f"Error loading interface data: {e}") from e
            exit(0)
        
        return interface_data

    def load_routing_table(self, filename):
        # Load routing table from the file and return data structure
        routing_table = {}
        try:
            with open(filename, 'r') as file:
                for line in file.readlines():
                    # print("RLINE", line)
                    tokens = line.strip().split()
                    if len(tokens) == 4:
                        destination, next_hop, subnet_mask, interface = tokens
                        routing_table[destination] = {
                            'next_hop': next_hop,
                            'subnet_mask': subnet_mask,
                            'interface': interface
                        }
                    else:
                        print(f"Skipping invalid line in {filename}: {line}")

        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            exit(0)

        except Exception as e:
            raise RuntimeError(f"Error loading routing table data: {e}") from e
            exit(0)
        
        return routing_table

    def load_hostname_mapping(self, filename):
        # Load hostname mapping from the file and return data structure
        hostname_mapping = {}

        try:
            with open(filename, 'r') as file:
                for line in file.readlines():
                    # print("HLINE", line)
                    tokens = line.strip().split()
                    if len(tokens) == 2:
                        hostname, ip_address = tokens
                        hostname_mapping[hostname] = ip_address
                        hostname_mapping[ip_address] = hostname
                    else:
                        print(f"Skipping invalid line in {filename}: {line}")

        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            exit(0)
        
        except Exception as e:
            raise RuntimeError(f"Error loading hosts data: {e}") from e
            exit(0)
        
        return hostname_mapping

    def connect_to_lans(self):
        # Connect to LANs specified in the interface file
        for interface in self.interface_data:
            # print("CONNECTED TO", interface)
            bridge_ip, bridge_port = self.get_bridge_info(self.interface_data[interface]['lan_name'])
            self.establish_tcp_connection(interface, bridge_ip, bridge_port, self.interface_data[interface]['lan_name'])

    def get_bridge_info(self, lan):
        # Read symbolic link files to get bridge IP and port

        # print(lan)

        lan_ip_link = f"{lan}.addr"
        lan_port_link = f"{lan}.port"

        try:
            # Read LAN IP address from symbolic link
            lan_ip_address = os.readlink(lan_ip_link)
            
            # Read LAN port from symbolic link
            lan_port = os.readlink(lan_port_link)

            return lan_ip_address, int(lan_port)

        except FileNotFoundError:
            print(f"Error: Symbolic link files not found for LAN {lan}.")
            exit(0)
        
        return None, None

    def establish_tcp_connection(self, interface, bridge_ip, bridge_port, lan_name):
        # Establish TCP connection to the specified bridge

        # print(bridge_ip, bridge_port, "TCP CONN")
        
        for i in range(6) :

            if i == 5 :
                print("Connection cannot be established")
                print("Exiting....")
                exit(0)

            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except Exception as e:
                print("Error: Creating Client Socket")
                if i <= 4 : print(f"{i}/5 -- Retrying....")
                continue

            try : 
                client.connect((bridge_ip, bridge_port))
            except Exception as e: 
                print(f"Error establishing connection: {e} : {bridge_ip}:{bridge_port}")
                if i <= 4 : print(f"{i}/5 -- Retrying....")
                continue

            response = client.recv(1024).decode('utf-8').strip()
            if response == "accept":
                # client.send(interface.encode('utf-8'))
                # threading.Thread(target=self.listen_to_bridge, args=(sock, interface)).start()
                self.client_socket[lan_name] = client
                print(f"Connected ~ {lan_name}")
                break
            elif response == "reject":
                print(f"Connection to {lan_name} rejected.")
                if i <= 4 : print(f"{i}/5 -- Retrying....")

    def send_message(self, source, dest_name, message):
        ###
        ## get source_ip, destination_ip
        ## get source_mac, destination_mac
        ## add them as header to message
        ###

        for i in self.interface_data:
            source_ip, source_mac, lan_name = self.interface_data[i]["ip_address"], self.interface_data[i]["mac_address"], self.interface_data[i]["lan_name"]

            destination_ip = self.hostname_mapping[dest_name]
            # next_hop = self.routing_table[destination_ip]
            if destination_ip not in self.arp_cache:
                ###
                ## UPDATE ARP CACHE
                ###
                self.pending_packets.append((source_ip, destination_ip, self.client_socket[lan_name], message))
                self.update_arp_cache()
                # print(self.arp_cache)
            
            # destination_mac = self.arp_cache[destination_ip]
            # dataframe = f"{source_mac}~{destination_mac}~{source_ip}~{destination_ip}~{message}"
            # self.client_socket[lan_name].send(dataframe)

            else :
                destination_mac = self.arp_cache[destination_ip][0]
                dataframe = f"{source_mac}~{destination_mac}~{source_ip}~{destination_ip}~{message}"
                # print(dataframe)
                if self.pending_packets :
                    self.pending_packets.append((source_ip, destination_ip, self.client_socket[lan_name], message))
                else :
                    self.client_socket[lan_name].send(dataframe.encode('utf-8'))


    def run(self):
        # Main loop of the station
        # signal.signal(signal.SIGINT, sigint_handler)
        self.connect_to_lans()

        while True :
            inputs = [self.client_socket[i] for i in self.client_socket]
            inputs.append(sys.stdin)
            client_sockets = [self.client_socket[i] for i in self.client_socket]
            read_sockets, _, _ = select.select(inputs, [], [])

            # print(client_sockets)

            for sock in read_sockets:
                if sock in client_sockets:
                    # print("++++++++++++++++++++++++")
                    # print("   RECIEVED MESSAGE")
                    # print("+++++++++++++++++++++++")
                    # recieve message from the server
                    message = sock.recv(4096).decode('utf-8').strip()
                    # print(message)
                    if not message:
                        pass

                    # if message is exit signal
                    if message.strip().startswith("[e]~"):
                        lan_name = message.replace("[e]~", "").strip()
                        print(f"{lan_name} Disconnected .... ")
                        del self.client_socket[lan_name]
                        sock.close()
                        ###
                        ## NEED TO EXIT ONLY IF ALL THE LANS CONNECTING ARE DISCONNECTED
                        ###
                        if not self.client_socket:
                            exit(0)
                    else:
                        self.handle_message(message, sock)
                else:
                    # User input from the keyboard
                    user_msg = sys.stdin.readline()
                    print("input:", user_msg.strip())

                    if user_msg.strip() == "":
                        continue
                    
                    ###
                    ## HANDLE OTHER COMMANDS FROM USER
                    ###
                    elif user_msg.strip() == "[e]" :
                        print("Disconnecting from bridge ... ")
                        msg = "src_mac~dest_mac~src_ip~dest_ip~" + ("[E]" if is_router else "[e]")
                        for s in self.client_socket : 
                            self.client_socket[s].send(msg.encode('utf-8'))
                        for s in self.client_socket :
                            self.client_socket[s].close()
                        sys.exit(0)

                    elif user_msg.strip() == "[h]" :
                        print("Commands: ")
                        print("[e] -- exit")
                        print("[h] -- help")
                        print("show arp -- shows arp table")
                        print("show ifaces -- shows interface details")
                        print("show rtable -- shows routing table")
                        print("show queue -- gives out the pending_packets queue")
                        if not self.is_router:
                            print("send dest_usr message -- sends message to dest_usr")
                    
                    elif user_msg.strip() == "show arp" : 
                        # print(self.arp_cache)
                        
                        print("-"*43)
                        print("|", "ip address".center(20), "|", "MAC".center(20), "|", sep="")
                        print("-"*43)

                        for i in self.arp_cache :
                            print("|", str(i).center(20), "|", str(self.arp_cache[i][0]).center(20), "|", sep = "")

                        print("-"*43)

                    elif user_msg.strip() == "show hosts" :
                        # print(self.hostname_mapping)

                        print("-"*33)
                        print("|", "hostname".center(10), "|", "IP".center(20), "|", sep= "")
                        print("-"*33)

                        for i in self.hostname_mapping:
                            if "." not in i:
                                print("|", str(i).center(5), "|", str(self.hostname_mapping[i]).center(20), "|", sep = "")
                        
                        print("-"*33)

                    elif user_msg.strip() == "show ifaces" : 
                        # print(self.interface_data)

                        print("-"*96)
                        print("|", "host".center(10), "|", "IP".center(20), "|", "SUBNET".center(20), "|", "MAC".center(20), "|", "LAN".center(20), "|", sep = "")
                        print("-"*96)
                        

                        for i in self.interface_data:
                            print("|", str(i).center(10), "|", "|".join([str(self.interface_data[i][j]).center(20) for j in self.interface_data[i]]), "|", sep = "")

                        print("-"*96)

                    elif user_msg.strip() == "show rtable" : 
                        # print(self.routing_table)

                        print("-"*80)
                        print("|", "DEST IP".center(20), "|", "NEXT HOP".center(20), "|", "SUBNET".center(20), "|", "LAN".center(20), "|", sep = "")
                        print("-"*80)
                        
                        for i in self.routing_table:
                            print("|", str(i).center(20), "|", "|".join([str(self.routing_table[i][j]).center(20) for j in self.routing_table[i]]), "|", sep = "")
                        
                        print("-"*80)



                    elif user_msg.strip() == "show queue" :
                        # shows pending queue
                        print(self.pending_packets)
                    
                    ###
                    ## SEND MESSAGE TO DESTINATION
                    ###
                    elif user_msg.strip().lower().startswith("send") :
                        if self.is_router:
                            print("Router cannot send Messages to users")
                            continue
                        # handle message
                        send, dest_name, message = user_msg.strip().split(" ", 2)
                        for i in self.client_socket:
                            self.send_message(self.client_socket[i], dest_name, message)
                    
                    else :
                        print("given command is invalid")
                        print("Commands: ")
                        print("[e] -- exit")
                        print("[h] -- help")
                        print("show arp -- shows arp table")
                        print("show ifaces -- shows interface details")
                        print("show rtable -- shows routing table")
                        print("show queue -- gives out the pending_packets queue")
                        if not self.is_router:
                            print("send dest_usr message -- sends message to dest_usr")
            
            self.process_pending_packets()
            self.check_arp_timeout()

    
    def check_arp_timeout(self) :
        for i in self.arp_cache :
            if self.arp_cache[i][1] == -1 :
                continue

            if time.time() - self.arp_cache[i][1] > 60 :
                self.arp_cache[i] = ()

        self.arp_cache = {i : self.arp_cache[i] for i in self.arp_cache if self.arp_cache[i]}

    
    def update_arp_cache(self) :
        for i in self.interface_data:
            src_ip, src_mac, lan_name = source_ip, source_mac, lan_name = self.interface_data[i]["ip_address"], self.interface_data[i]["mac_address"], self.interface_data[i]["lan_name"]

            arp_req = f"{src_mac}~broadcast~{src_ip}~broadcast~ARP REQUEST"

            self.client_socket[lan_name].send(arp_req.encode('utf-8'))

    def handle_message(self, message, sock):

        if not message.strip() : return 

        if self.is_router:
            self.route_message(message, sock)
            return

        src_mac, dest_mac, src_ip, dest_ip, message = message.strip().split("~", 5)

        self.arp_cache[src_ip] = (src_mac, time.time())

        if message == "ARP REQUEST":

            # print("****************************************")
            # print("|             ARP REQUEST              |")
            # print("****************************************")

            dest_ip, dest_mac = src_ip, src_mac
            for i in self.interface_data :
                if self.client_socket[self.interface_data[i]["lan_name"]] == sock :
                    # print("****************************************")
                    # print("|             FOUND   ARP              |")
                    # print("****************************************")
                    src_ip, src_mac = self.interface_data[i]["ip_address"], self.interface_data[i]["mac_address"]

                    message = f"{src_mac}~{dest_mac}~{src_ip}~{dest_ip}~ARP REPLY"

                    sock.send(message.encode('utf-8'))

                    # print("****************************************")
                    # print("|             SENDING ARP              |")
                    # print("****************************************")
            
            # print("****************************************")
            # print("|             FOUND   ARP              |")
            # print("****************************************")
            # src_ip, src_mac = self.interface_data[i]["ip_address"], self.interface_data[i]["mac_address"]

            # message = f"{src_ip}~{dest_ip}~{src_mac}~{dest_mac}~ARP REPLY"

            # sock.send(message)

            # print("****************************************")
            # print("|             SENDING ARP              |")
            # print("****************************************")

            

        elif message == "ARP REPLY" :
            # Already updated the ARP CACHE
            # print("****************************************")
            # print("|            RECIEVED ARP              |")
            # print("****************************************")
            pass

        else :
            for i in self.interface_data:
                if dest_ip == self.interface_data[i]["ip_address"] :
                    print(self.hostname_mapping[src_ip], ":", message)

    
    def process_pending_packets(self):
        
        if not self.pending_packets :
            return 

        for i in range(len(self.pending_packets)) :
            src_ip, dest_ip, sock, message = self.pending_packets[i]

            if dest_ip not in self.arp_cache:
                # print(dest_ip, "not in", self.arp_cache)
                continue

            src_mac = self.arp_cache[src_ip][0]
            dest_mac = self.arp_cache[dest_ip][0]

            dataframe = f"{src_mac}~{dest_mac}~{src_ip}~{dest_ip}~{message}"

            try :
                sock.send(dataframe.encode('utf-8'))
                self.pending_packets[i] = 0
            
            except :
                self.pending_packets[i] = 0

        
        self.pending_packets = [i for i in self.pending_packets if i]

    def route_message(self, message, sock):
        ###
        ## ROUTE MESSAGE TO DEST PORT
        ###
        # print("****************************************")
        # print("|           ROUTING MESSAGE            |")
        # print("****************************************")

        ###
        ## IF MESSAGE IS ARP REQUEST DISTRIBUTE
        ###
        src_mac, dest_mac, src_ip, dest_ip, msg = message.strip().split("~", 5)

        self.arp_cache[src_ip] = (src_mac, time.time())

        if not msg.startswith("ARP") : 
            print(self.hostname_mapping[src_ip], "-->", self.hostname_mapping[dest_ip] )


        self.route_ip[src_ip] = sock

        # if msg.strip().startswith("ARP"):
        if dest_ip in self.route_ip :
            self.route_ip[dest_ip].send(message.encode("utf-8"))

        else:
            for i in self.client_socket:
                if self.client_socket[i] != sock :
                    # print("****************************************")
                    # print("|         DISTRIBUTE ARP MSG           |")
                    # print("****************************************")
                    self.client_socket[i].send(message.encode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) == 5 :
        station_cond = sys.argv[1]
        interface_file = sys.argv[2]
        routing_file = sys.argv[3]
        hosts_file = sys.argv[4]
        is_router = False

        # signal.signal(signal.SIGINT, sigint_handler)

        if station_cond == "-no" :

            station = Station(interface_file, routing_file, hosts_file, is_router)
            # signal.signal(signal.SIGINT, sigint_handler)
            station.run()

        elif station_cond == "-route" :
            ###
            ## IS A ROUTER
            ###
            is_router = True
            station = Station(interface_file, routing_file, hosts_file, is_router)
            # signal.signal(signal.SIGINT, sigint_handler)
            station.run()
        
        else :
            print("USAGE::")
            print("STATION: python3 station -no ifaces rtable hosts")
            print("ROUTER: python3 station -route iface rtable hosts")
        
    else :
        print("USAGE::")
        print("STATION: python3 station -no ifaces rtable hosts")
        print("ROUTER: python3 station -route iface rtable hosts")
