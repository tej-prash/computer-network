import socket
import time
import os
import threading
import sys
import queue
import select
import traceback
#from multiprocessing import Queue
# Take input from admin

#file_no=input("Enter the file name to be sent\n")
#fp= open(file_no)
fp = open("script.sh")
text = fp.readlines()
for ele in range(0, len(text)):
    text[ele] = str(ele)+","+text[ele]
# Send heartbeats to indicate clients which require the file
ipaddress = []

# Server
server_port = 9876
client_port = 1234

server_ip = '127.0.2.15'
# List of python sockets that can be read
inputs = []
# list of python sockets that can be written into
outputs = []

# Server keeps track of command number for each client
command_failed = dict()
# Key-IP address
# Value-list of failed command counts

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setblocking(0)
#s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((server_ip, server_port))
# s.connect(('10.10.1.1',1234))

serversocket.listen(5)
inputs = [serversocket]
outputs = []
message_queues = {}  # dictionary
try:
    while inputs:
        print("Waiting for events")
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs, 10.0)
        for s in readable:
            if s is serversocket:
                connection, client_address = s.accept()
                ipaddress.append(client_address)
                connection.setblocking(0)
                print("new connection added")
                inputs.append(connection)
                message_queues[connection] = queue.Queue()

                send_data = "".join(text)  # sends (command_no,data)
                message_queues[connection].put(send_data)
                if connection not in outputs:
                    outputs.append(connection)
                # connection.send(text)
            else:
                received = s.recv(1000).decode().split(",")
                if(received[0] == ''):
                    break
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
                        send_data = "".join(
                            [text[i] for i in range(len(text)) if i == int(command_no)])
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
                    s.close()
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
                    #del message_queues[s]
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
