# Client code for Auto Software Installation

import socket
import os
import select
import sys
import queue
import traceback
import struct, fcntl
import logging

try:
	logging.basicConfig(filename="log/alog.log", level=logging.DEBUG,
	                    format='%(asctime)s - %(levelname)s : %(message)s')
except:
    os.system("mkdir log")
    logging.basicConfig(filename='log/alog.log',level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s : %(message)s')


server_port = 9876
client_port = 1234
# server_address = '10.1.10.131'
server_address = '127.0.0.1'

# Creating a TCP/IP socket.
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Function to get self-IP address.
sockfd = sock.fileno()
SIOCGIFADDR = 0x8915
def get_ip(iface = 'enp2s0'):
	ifreq = struct.pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
	try:
		res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
	except:
		return None
	ip = struct.unpack('16sH2x4s8x', res)[2]
	return socket.inet_ntoa(ip)


client_address = get_ip('enp2s0')
if client_address is None:
    # Default client address
    client_address = '127.0.0.1'



# Ensuring 'Binding Socke: "Address already is use"' error is not thrown.
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Binding ip address of client itself
sock.bind((client_address, client_port))

# Connection establishment from client to server.
sock.connect((server_address, server_port))

# Variable to keep track of the number of times commands are re-executed.
# Key : command_no
# Value : re-executed_count
command_count = dict()  # Type: Dict[int, int]

# List of python sockets that can be read
inputs = [sock]

# List of python sockets that can be written into
outputs = []

# Outgoing message queue
# Key : socket
# Value : Queue
message_queues = {}  # Type: Dict[object, object]

try:
    while inputs:
        print("Waiting for events...")
        logging.info("Waiting for events...")
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 10.0)

        flag = 0
        for s in readable:
            # If s is the main server socket, the server is ready to accept incoming connections
            if s is sock:
                data = s.recv(2000).decode()
                print("Data received", data)
                if data != '':
                    logging.info("Data received")

                    # Give the connection a queue for data we want to send
                    message_queues[s] = queue.Queue()

                    commands = data.strip().split("\n")
                    commands = [i.split(",") for i in commands]


                    for cmd_num, command in commands:
                        # subprocess call to execute command
                        retval = os.system(command)

                        # Non-zero return value indicates error
                        if(retval != 0):
                            flag = retval
                            # TODO: CHECK IF its command_count[s] or command_count[cmd_num]

                            # Check number of times the command is executed
                            if(s in command_count.keys()):
                                if(command_count[s] > 3):
                                    # FAIL status sent back.
                                    logging.info("Command FAILED permanently")
                                    message_queues[s].put(
                                        str(cmd_num)+","+str("FAIL")+","+str(client_address))
                                    continue
                                else:
                                    logging.info("Command failed. Asking for resending")
                                    command_count[s] += 1
                            else:
                                command_count[s] = 0

                            message_queues[s].put(
                                str(cmd_num)+","+str(flag)+","+str(client_address))
                    else:
                        if(flag == 0):
                            print("All commands executed successfully")
                            logging.info("All commands executed successfully")
                            # Seding EOF on success
                            message_queues[s].put(
                                str(cmd_num)+","+str("EOF")+","+str(client_address))
                    if s not in outputs:
                        outputs.append(s)
                # if s in outputs:
                #     outputs.remove(s)
                # # inputs.remove(s)
                # s.close()
                # del message_queues[s]

        for s in writable:
            print("Sending ACK...")
            logging.info("Sending ACK...")
            try:
                next_msg = message_queues[s].get_nowait().encode('utf-8')
            except queue.Empty:
                outputs.remove(s)
            else:
            	if(flag==0):
                	s.send(next_msg)

        for s in exceptional:
            # If an error with a socket, we stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

except Exception as e:
    print(e)
    logging.error("Exception encountered!")
    traceback.print_exc()
    sock.close()
