from socket import * 
serverName="10.1.10.18"
serverPort=12000
clientSocket=socket(AF_INET,SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
length = clientSocket.recv(4096)
clientSocket.send("ack1")
print(length)
myfile = open("psutil-5.4.8.tar.gz", 'wb')
tl=0
data=b''
while(len(data) < int(length)):
    recv_data = clientSocket.recv(4096)
    print("data")
    tl=tl+len(recv_data)
    data+=recv_data
myfile.write(data)
print(len(data))
myfile.close()

