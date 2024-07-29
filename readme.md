###################################
\#\# DATA/COMPUTER COMMUN (CNT5505) \#\#
\#\#\#\#   Computer Science, FSU    \#\#\#\#
####################################

####################################
#------                           ##
#         NETWORK EMULATOR        ##
#                            ------#
####################################

+> The Netowrk Emulator software tool uses server-client pradigm where bridges are servers. Clients and Routers act as clients.
+> The stations(or routers)(i.e clients) establishes a connection with the bridge(server)

1. Author/email address

	Vivek Vardhan Reddy Yannam -- VY22@fsu.edu
        Kalyandeep Pidikiti -- KP22Y@fsu.edu

2. Code details

	platform: linux
	language: PYTHON3
    
    commands: 
    * run bridge -- python3 bridge.py lan-name num_ports
    * run station -- python3 station.py -no ifaces_file rtable_file hosts
    * run router -- python3 station.py -route ifaces_file rtable_file hosts

3. Commands supported in stations/routers/bridges

   3.1 stations:

	   send <destination> <message> // send message to a destination host
	   show arp 		## show the ARP cache table information
	   show queue 		## show the pending_queue
	   show	hosts 		## show the IP/name mapping table
	   show	ifaces 		## show the interface information
	   show	rtable 		## show the contents of routing table
	   [e] 			## close the station
	   [h] 			## help

   3.2 routers:

	   show	arp 		## show the ARP cache table information
	   show	queue		## show the pending_queue
	   show	hosts 		## show the IP/name mapping table
	   show	ifaces 		## show the interface information
	   show	rtable 		## show the contents of routing table
	   [e] 			## close the router
           [h] 			## help


   3.3 bridges:

	   show sl 		## show the contents of self-learning table
	   [e] 			## close the bridge
           [h] 			## help


4. To start the emulation, run

   	run_simulation contains commands, which emulates the following network topology

   
          B              C                D
          |              |                |
         cs1-----R1------cs2------R2-----cs3
          |                               |
          A                               E

    cs1, cs2, and cs3 are bridges.
    R1 and R2 are routers.
    A to E are hosts/stations.

5. Components

    5.1 Bridge - 
       The BRIDGE in a network forwards data frames between different LAN segments. 
        Functions of a bridge include: 
             - filter and forward frames based on MAC addresses 
             - self-learning to dynamically adapt to network changes.
        Incase if the given lan_name is already present, the program asks for new lan_name

    5.2 Router - 
       A router is a specialized component designed to connect various local area networks (LANs) 
       It also facilitate the routing of data packets between bridges. 

    5.3 Station - 
       the main functionalities of a station:
       - Sending messages and ARP requests, and 
       - Encapsulating the message into IP packets and ethernet frames. 
       For message transmission, stations act as both source and destination points.

