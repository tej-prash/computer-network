# Server code for Auto Software Installation

import socket
import time
import os
import threading
import sys
import queue
import select
import traceback
import logging

try:
	logging.basicConfig(filename="log/alog.log", level=logging.DEBUG,
	                    format='%(asctime)s - %(levelname)s : %(message)s')
except:
    os.system("mkdir log")
    logging.basicConfig(filename='log/alog.log',level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s : %(message)s')

# TODO: link with front end - Drag n drop

fp = open("script.sh")
text = fp.readlines()

# Each ele in text is of form str(command_no, data)
# Zero indexed scheme is used for numbering.
for ele in range(0, len(text)):
    text[ele] = str(ele)+","+text[ele]

# Send heartbeats to indicate clients which require the file
ipaddress = []  # Type: List[str]
server_port = 9876
client_port = 1234
# server_ip = '10.1.10.131'
server_ip = '127.0.0.1'

# Variable to keep track of the number of times commands are re-executed
# Key : socket object
# Value : list of failed command counts
command_failed = dict()  # Type: Dict[socket object, List]

# Creating a TCP/IP socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setblocking(0)

# Ensuring 'Binding Socke: "Address already is use"' error is not thrown
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the port
serversocket.bind((server_ip, server_port))

serversocket.listen(5)

# List of python sockets that can be read
inputs = [serversocket]

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

        for s in readable:
            # If s is the main server socket, the server is ready to accept incoming connections
            if s is serversocket:
                connection, client_address = s.accept()
                ipaddress.append(client_address)
                connection.setblocking(0)
                inputs.append(connection)
                print("New connection added.")
                logging.info("New connection added.")

                # Give the connection a queue for data we want to send
                message_queues[connection] = queue.Queue()

                send_data = "".join(text)  # sends (command_no,data)
                message_queues[connection].put(send_data)
                if connection not in outputs:
                    outputs.append(connection)

            # If it enters the else clause, it means there is an established connection with client
            else:
                data = s.recv(10000).decode().split("\n")
                for i in data:
                    received = i.split(",")
                    if(received[0] == ''):
                            break
                    print("Received data from client", received)
                    logging.info("Received data from client")

                    # The server recieves command_no, status, ip_addr.
                    command_no, status, ip_addr = received
                    if status != 'EOF':
                            # We send status as FAIL after retrying it 3 times
                            if status == 'FAIL':
                                   #####print("Error occured in command: ", text[int(command_no)])
                                    logging.error("Error occured in command: %s", text[int(command_no)])
                                    if(s in command_failed.keys()):
                                            command_failed[s].append(command_no)
                                    else:
                                            command_failed[s] = [command_no]

                            # We retry failed commands 3 times to be sure they are failing for legitimate reasons.
                            elif(int(status) != 0):
                                print("Failed to execute commands on ", ip_addr)
                                logging.info(" Failed to execute commands on %s",ip_addr)
                                send_data = "".join([text[i] for i in range(len(text)) if i == int(command_no)])
                                print("Retrying failed commands...")
                                logging.info("Retrying failed commands...")
                                message_queues[s].put(send_data)

                            # If it reaches here commands must have executed successfully
                            else:
                                    print("Commands executed successfully")
                                    logging.info("Commands executed successfully")

                    # A readable socket without data is available
                    # EOF is received. Stream ready to be closed
                    else:
                            print("EOF : Terminating connection with client")
                            logging.info("EOF : Terminating connection with client")
                            if s in outputs:
                                    outputs.remove(s)
                            inputs.remove(s)
                            writable.remove(s)
                            # s.close()
                            del message_queues[s]

        for s in writable:
            if s is not serversocket:
                try:
                    next_msg = message_queues[s].get_nowait().encode('utf-8')
                except queue.Empty:
                    print("Queue is empty")
                    logging.info("Queue is empty")
                else:
                    print("Sending data")
                    print(next_msg)
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
    serversocket.close()
