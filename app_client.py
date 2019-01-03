from socket import *
import psutil
import time
import os
import datetime
import re, uuid 
from threading import Thread
import logging
cmac=':'.join(re.findall('..', '%012x' % uuid.getnode()))
f = open("issues.txt",'w')
f.write(cmac)
f.close()
try:	
	logging.basicConfig(filename="log/log.log",level=logging.DEBUG,format='%(asctime)s - %(levelname)s : %(message)s')
except:
	os.system("mkdir log")
	logging.basicConfig(filename='log/log.log',level=logging.DEBUG,format='%(asctime)s - %(levelname)s : %(message)s')
logging.info("Start")	
logging.info("MAC ADDRESS "+cmac)
flag=0
ef=0
serverName='10.1.10.18'
serverPort=12000
clientSocket=socket(AF_INET,SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
#clientSocket.send(sentence)
#allowed=["python","gedit","bash"]
def check_ts(data_ts):
    print(data_ts)
    time_data=data_ts.split(".")
    print(time_data)
    st=int(time_data[0])
    st2=int(time_data[1])
    et=int(time_data[2])
    et2=int(time_data[3])
    st3=st*60+st2
    et3=et*60+et2
    global flag
    while 1:
        now = datetime.datetime.now()
        hr=int(now.hour)
        minute=int(now.minute)
        cur=hr*60+minute
        print(hr,minute,cur)
        if((st3<=cur) and (et3>=cur)):
            flag=1
        else:
            flag=0
        time.sleep(1*60)
while 1:
	server_pkt=clientSocket.recv(2048)
	if(server_pkt!="nk"):
		allowed=server_pkt.split(",")
		server_pkt=allowed
		print(server_pkt)
		if(server_pkt[-1]=="shutdown"):
			os.system("shutdown -h now")
		if(server_pkt[-1]==".log" or server_pkt[-1]==".jpg"or server_pkt[-1]==".txt"):
			opt=server_pkt[-1]
			print(opt)
			if(opt==".log"):
				fil="log/log.log"	
			elif(opt==".jpg"):
				fil="temp.jpg"
				os.system("import -window root "+fil)
				time.sleep(2)
			else:
				fil="issues.txt"
			myfile1 = open(fil, 'rb')
			bytes = myfile1.read()
			myfile1.close()
			print("Total bytes:",len(bytes))
			clientSocket.sendall(str(len(bytes)))
			ack=clientSocket.recv(1024)
			print(ack)
			myfile = open(fil, 'rb')
			clientSocket.sendall(bytes)
		elif(server_pkt[-1]=="t"):
			flag=1
		elif(server_pkt[-1]=="ts"):
			t1=Thread(target=check_ts,args=(server_pkt[-2],))
			t1.start()
		elif(server_pkt[-1]=="m"):
			cmac=':'.join(re.findall('..', '%012x' % uuid.getnode()))
			print(cmac)
			clientSocket.send(cmac)
		else:
		#allowed=server_pkt.split(",") 
			#print(allowed)
			for proc in psutil.process_iter(attrs=['pid','name']):
				if(proc.name()=="bash"):	
					flag=1;
				if(flag==1 and proc.name() not in allowed):
					print(proc.pid,proc.name())
					p=psutil.Process(proc.pid)
					try:
						pid=proc.pid
						pname=proc.name()
						p.terminate()
						logging.info("Killed:"+str(pid)+" "+pname)
						ef=1
					except:
						print("Error killing")
						logging.error("Error Killing:"+str(proc.pid)+" "+proc.name())
						ef=1
				if(flag==1 and ef!=1):
					logging.info("Allowed:"+str(proc.pid)+" "+proc.name())
			ef=0
			flag=0
		#	time.sleep(20)
		#clientSocket.close()
	else:
		continue
