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

# TODO: link with front end - Drag n drop.

fp = open("script.sh")
text = fp.readlines()
for ele in range(0, len(text)):
    text[ele] = str(ele)+","+text[ele]

# Send heartbeats to indicate clients which require the file
ipaddress = []
server_port = 9876
client_port = 1234
server_ip = '10.1.10.131'

# Variable to keep track of the number of times commands are re-executed.
# Key : IP address.
# Value : list of failed command counts.
command_failed = dict()  # Type : Dict[str, List]

# Creating a TCP/IP socket.
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setblocking(0)

# Ensuring 'Binding Socke: "Address already is use"' error is not thrown.
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the port.
serversocket.bind((server_ip, server_port))

serversocket.listen(5)

# List of python sockets that can be read.
inputs = [serversocket]

# List of python sockets that can be written into.
outputs = []

# Outgoing message queue.
# Key : socket
# Value : Queue
message_queues = {}  # Type : Dict[object, object]

try:
    while inputs:
        print("Waiting for events...")
        logging.info("Waiting for events...")
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 10.0)
        for s in readable:
            # If s is the main server socket, the server is ready to accept incoming connections.
            if s is serversocket:
                connection, client_address = s.accept()
                ipaddress.append(client_address)
                connection.setblocking(0)
                print("New connection added.")
                logging.info("New connection added.")
                inputs.append(connection)

                #Give the connection a queue for data we want to send.
                message_queues[connection] = queue.Queue()

                send_data = "".join(text)  # sends (command_no,data)
                message_queues[connection].put(send_data)
                if connection not in outputs:
                    outputs.append(connection)
                # connection.send(text)
            else:
                data = s.recv(10000).decode().split("\n")
                for i in data:
                        received = i.split(",")
                        if(received[0] == ''):
                                break
                        print("Received ", received)
                        command_no, status, ip_addr = received
                        if status != 'EOF':
                                if status == 'FAIL':
                                        if(s in command_failed.keys()):
                                                command_failed[s].append(command_no)
                                        else:
                                                command_failed[s] = [command_no]
                                        continue
                                print("Error occured in command: ", text[int(command_no)])
                                if(int(status) != 0):
                                    print("Failed to execute commands on ", ip_addr)
                                    send_data = "".join([text[i] for i in range(len(text)) if i == int(command_no)])
                                    print("Resending:", send_data)
                                    message_queues[s].put(send_data)
                                else:
                                        print("Commands executed sucessfully")
                                # if s not in outputs:
                                # outputs.append(s)
                        else:
                                print("Removing s from inputs and outputs")
                                if s in outputs:
                                        outputs.remove(s)
                                inputs.remove(s)
                                writable.remove(s)
                                # s.close()
                                del message_queues[s]

        for s in writable:
            print("Iterating through writable")
            if s is not serversocket:
                # print(message_queues[s].queue.get_nowait().encode('utf-8'))
                try:
                    next_msg = message_queues[s].get_nowait().encode('utf-8')
                except queue.Empty:
                    print("Queue is empty")
                    # outputs.remove(s)
                else:
                    print("Sending data")
                    print(next_msg)
                    s.send(next_msg)
                    # del message_queues[s]
                    # outputs.remove(s)
        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

except Exception as e:
    print(e)
    print("Exception encountered")
    traceback.print_exc()
    serversocket.close()
