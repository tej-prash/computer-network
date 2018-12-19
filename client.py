
import socket
import time
import os
import select
import sys
import Queue
import traceback
# Client

# server_address='10.10.1.2'
server_address = '10.0.2.15'
client_address = '10.0.2.30'
server_port = 9876

# binding hostname and port number to socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# ip address of client itself
# sock.bind(('10.10.1.1',1234))
sock.bind((client_address, 1234))

# udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
# udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# udp.bind(("",1234))

# get ip address and send
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
print(IPAddr)

#ip_length = len(IPAddr)
# if(len(str(ip_length))!=2):
#ip_length = '0'+str(ip_length)
#ip_length = ip_length.encode('utf-8')

# initiaztes TCP connection to send IP
sock.connect((server_address, server_port))
# sock.send((ip_length))
# IPAddr=IPAddr.encode('utf-8')
# sock.send((IPAddr))
# sock.close()
# time.sleep(5)


inputs = [sock]
outputs = []
message_queues = {}
try:
    while inputs:
        print("Waiting for events")
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs, 10.0)
        # time.sleep(2)
        for s in readable:
            if s is sock:
                data = s.recv(2000)
                print("Printing data", data)
                if data:
                    print("Received data")
                    message_queues[s] = Queue.Queue()
                    commands = data.split("\n")
                    flag = 0
                    for command in commands:
                        retval = os.system(command)
                        # send ACK
                        if(retval != 0):
                            flag = retval
                        # retval=str(retval)
                        # s.send(retval)
                    message_queues[s].put(
                        str(flag).encode('utf-8')+","+client_address)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    if s in outputs:
                        outputs.remove(s)
                    # inputs.remove(s)
                    s.close()
                    del message_queues[s]
            else:
                pass

        for s in writable:
            print("Sending ACK")
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                outputs.remove(s)
            else:
                if s in outputs:
                    outputs.remove(s)
                    del message_queues[s]
                s.send(next_msg)

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
    sock.close()
"""

try:
	while True:
	    #data, addr = udp.recvfrom(1024)
	    #print("received message: %s"%data)

	    #udp.sendto(IPAddr,(addr,server_port))
	    
	    #sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	    #sock.bind(('127.0.0.1',1234))
	    #sock.listen(1)
	    #clientsocket, addr=sock.accept()
		
            m=clientsocket.recv(2000)
            if not m
	    while(1):
		m = clientsocket.recv(3)
		if not m:
		    break
		#print("length ",int(m))
		if(m.decode()=='EOF'):
		    break
		command=clientsocket.recv(int(m))

		retval=os.system(command)
		#send ACK
		retval=str(retval)
		
		retval=retval.encode('utf-8')
		clientsocket.send((retval))"""
