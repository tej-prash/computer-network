import socket
import time
import os
import threading
import sys
import Queue
import select
import traceback

# Take input from admin

#file_no=input("Enter the file name to be sent\n")
#fp= open(file_no)
fp = open("script.sh")
# Send heartbeats to indicate clients which require the file
ipaddress = []

# Server
server_port = 9876
client_port = 1234

server_ip = '10.0.2.15'
# List of python sockets that can be read
inputs = []
# list of python sockets that can be written into
outputs = []

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setblocking(0)
#s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((server_ip, server_port))
# s.connect(('10.10.1.1',1234))

# UDP broadcasting
# udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
# udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# udp.sendto(b"initiate",('255.255.255.255',1234))
#data, addr = udp.recvfrom(15)


serversocket.listen(5)
inputs = [serversocket]
outputs = []
message_queues = {}
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
                message_queues[connection] = Queue.Queue()
                text = fp.readlines()
                print(text)
                message_queues[connection].put(text)
                if connection not in outputs:
                    outputs.append(connection)
                # connection.send(text)
            else:
                data, ip_addr = s.recv(30).decode().split(",")
                if data.decode('utf-8') != 'EOF':
                    print("Received data")
                    if(int(data) != 0):
                        print("Failed to execute commands on ", ip_addr)
                    else:
                        print("Commands executed sucessfully")
                    # message_queues[s].put(data)
                    # if s not in outputs:
                    # outputs.append(s)
                else:
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del message_queues[s]

        for s in writable:
            if s is not serversocket:
                print("Sending data")
                for ele in list(message_queues[s].queue):
                    print(ele)
                try:
                    next_msg = message_queues[s].get_nowait()
                except Queue.Empty:
                    outputs.remove(s)
                else:
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

# s.listen(1)
# serversocket,addr=s.accept()
#ip_addr_size = serversocket.recv(2)
#ip_addr_size = ip_addr_size.decode()
#ip_addr_size = int(ip_addr_size)
#ip_addr = serversocket.recv(ip_addr_size)
##ip_addr= ip_addr.decode()
# ipaddress.append(ip_addr)
# s.close()

"""print(ipaddress)
#I have ipaddress list at this point.

for ip in ipaddress:
    print(ip)
    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    time.sleep(1)
    s.bind(("127.0.0.1",server_port))
    s.connect((ip,client_port))
    client_code(fp)
    s.close()

# We start threads for every element in list.
def client_code(fp):
    for line in fp.readlines():
        #print(line)
        line=line.encode('utf-8')
        length=str(len(line))
        if(len(length)!=3):
            length=((3-len(length))*'0')+length
            #print(length)
            length= length.encode('utf-8')
            
        s.send((length))
        s.send((line))
        m=s.recv(2)
        m=m.decode()

        if(int(m)!=0):
            print("Failed to execute command: ",line.decode().strip())    
        else:
            print("Command succesfull! : ",line.decode().strip())
    s.send(("EOF".encode('utf-8')))
    print("Session Ended\n")    
"""
