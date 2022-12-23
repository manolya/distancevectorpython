import sys
import socket
from _thread import *
import threading
import time
import os 

print_lock = threading.Lock()
portout=[]
connected = []
costs = []
dvTable = []


def updateDvTable(data, numoflisten, portlisten):
    try:
        updatedDV = False
        chunks = data.strip().split('\n')
        neighborDV = []
        indx = 0
        nrows, ncols = (numoflisten, 2)
        #initiate the empty incoming dv table
        
        for i in range(numoflisten):
            coln = []
            for j in range(2):
                coln.append(0)
            neighborDV.append(coln)
        #fill the incoming dv table from the data received
        cliPort = 0
        cliCostOrig = 0
    
        for chunk in chunks:
            temp = chunk.split()
            if temp[1] == '0':
                cliPort = int(temp[0])
            neighborDV[indx][0] = int(temp[0])
            if temp[1] == 'inf':
                neighborDV[indx][1] = float('inf')
            else:
                neighborDV[indx][1] = int(temp[1])
            indx += 1
        #update the table
        hops = []
        for port in dvTable:
            if port[0] == cliPort:
                cliCostOrig = port[1]
        for neigh in neighborDV:
            if neigh[0] == portlisten:
                hops.append(0)
                continue
            if neigh[1] == float('inf'):
                hops.append(float('inf'))
            elif cliCostOrig == 'inf':
                hops.append(float('inf'))
            else:
                hops.append(cliCostOrig + neigh[1])

        for i in range(len(dvTable)):
            temp = float(hops[i])
            if temp < float(dvTable[i][1]):
                updatedDV = True
                if temp == float('inf'):
                    dvTable[i][1] = float('inf')
                else:
                    dvTable[i][1] = int(temp)

        if updatedDV:
 
            for i in range(len(connected)):
                connected[i] = False
    except Exception as e:
        print_lock.acquire()
        print(e)
        print_lock.release()
 
 

def listenThread(host, port, numoflisten):
    try:
        socklisten = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socklisten.bind((host, port))
        socklisten.listen(numoflisten)
        while True:
            socklisten.settimeout(5.0)
            conn, addr = socklisten.accept()
            out = False
            
            while True:
                try: 
                    data = conn.recv(1024)
                    
                    updateDvTable(data.decode('ascii'), numoflisten, port)
                    break
                except (socket.error, e):
                    print(socket.error)
            if out:
                break
            socklisten.settimeout(None)


        socklisten.close()
    except socket.timeout:
        print_lock.acquire()
        for i in range(len(dvTable)):
            print(str(port) + ' - ' + str(dvTable[i][0]) + ' | ' + str(dvTable[i][1]))
        print_lock.release()
        socklisten.close()
        os._exit(0)
    except:
        print_lock.acquire()
        print("some fault occurred")
        print_lock.release()
        socklisten.close()
        os._exit(0)

def sendThread(host, numoflisten):
    while True:
        for portidx in range(len(portout)):
            if connected[portidx]:
                continue
            try:
                port = portout[portidx] 
                socksend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socksend.connect((host, port))
                connected[portidx] = True
                inpdata = ''
                for i in range(numoflisten):
                    inpdata += str(dvTable[i][0]) + ' ' + str(dvTable[i][1]) + '\n'
                print_lock.acquire()
                socksend.send(inpdata.encode('ascii'))
                print_lock.release()
                socksend.close()
            except:
                pass

         

def Main():
    host = 'localhost'
    portthis = int(sys.argv[1])
    f = open(str(portthis)+".costs", "r")
    try:
        numoflisten = int(f.readline().strip()) 
        for lines in f:
            vals = lines.strip().split()
            portout.append(int(vals[0]))
            costs.append(int(vals[1]))
            connected.append(False)
    except:
        print("file is not properly structured")
        sys.exit(0)
    
    dvrows, dvcols = (numoflisten, 2)
    for i in range(dvrows):
        col=[3000+i]
        for j in range(dvcols - 1):
            col.append(float('inf'))
        dvTable.append(col) 
    indx = 0
    while indx < numoflisten:
        if dvTable[indx][0] == portthis:
            dvTable[indx][1] = 0
        elif dvTable[indx][0] in portout:
            tempix = portout.index(dvTable[indx][0])
            dvTable[indx][1] = costs[tempix]
        indx += 1
    try: 
        t_server = threading.Thread(target=listenThread, args=(host, portthis, numoflisten, )).start()
        t_client = threading.Thread(target=sendThread, args=(host, numoflisten, )).start()
    except:
        os._exit(0)
if __name__ == '__main__':
    Main()
