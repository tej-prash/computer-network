# Client code for Auto Software Installation

import socket
import os
import select
import sys
import queue
import traceback
import struct, fcntl

server_address = '10.1.10.131'
server_port = 9876
client_port = 1234

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

# Ensuring 'Binding Socke: "Address already is use"' error is not thrown.
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Binding ip address of client itself
sock.bind((client_address, client_port))

# Connection establishment from client to server.
sock.connect((server_address, server_port))

# Variable to keep track of the number of times commands are re-executed.
command_count = dict()  # Type: Dict[command_no, re-executed_count]

inputs = [sock]  #Type: List[sockets]
outputs = []
message_queues = {}
try:
    while inputs:
        print("Waiting for events")
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs, 10.0)
        # time.sleep(2)
        flag = 0
        for s in readable:
            if s is sock:
                data = s.recv(2000).decode()
                print("Printing data", data.encode('utf-8'))
                if data != '':
                    print("Received data")
                    message_queues[s] = queue.Queue()
                    commands = data.strip().split("\n")
                    commands = [i.split(",") for i in commands]

                    # print(commands[1])
                    for cmd_num, command in commands:
                        retval = os.system(command)
                    # send ACK
                        if(retval != 0):
                            # Send status error
                            flag = retval

                            # Check number of times command is exeucted
                            if(s in command_count.keys()):
                                if(command_count[s] > 3):
                                    # Command failure
                                    message_queues[s].put(
                                        str(cmd_num)+","+str("FAIL")+","+str(client_address))
                                    continue
                                else:
                                    command_count[s] += 1
                            else:
                                command_count[s] = 0
                                # retval=str(retval)
                            message_queues[s].put(
                                str(cmd_num)+","+str(flag)+","+str(client_address))
                    else:
                        if(flag == 0):
                            print("All commands executed successfully")
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
            print("Sending ACK")
            try:
                next_msg = message_queues[s].get_nowait().encode('utf-8')
            except queue.Empty:
                outputs.remove(s)
                # if s in outputs:
                #     outputs.remove(s)
                #     del message_queues[s]
            else:
            	if(flag==0):
                	s.send(next_msg)
                	#inputs.remove(s)
                	#if s in outputs:
                	#	outputs.remove(s)
                	#s.close()
                	#del message_queues[s]
        #print("hello")
        for s in exceptional:
            print("exception")
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]
except Exception as e:
    print(e)
    print("Exception encountered")
    traceback.print_exc()
    sock.close()
