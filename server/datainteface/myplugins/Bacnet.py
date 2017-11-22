#!/usr/bin/ python
# -*- coding: utf-8 -*-
#
#

import time
import signal,sys,os
import getopt
#from multiprocessing.dummy import Pool as ThreadPool 
from IPy import IP
import threading
import socket
import string,struct
import BACNetlib2

BUFSIZE = 10240	#缓冲区大小10k

mylock = threading.Lock()  #Allocate a lock
ISOTIMEFORMAT='%Y-%m-%d_%X'

def ip2long(ip):
    """
    Convert an IP string to long
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

def long2ip(ip_long):
    return socket.inet_ntoa(struct.pack('!L', ip_long))


def dataSwitch(data):
    str1 = ''
    str2 = ''
    while data:
        str1 = data[0:2]
        s = int(str1,16)
        str2 += struct.pack('B',s)
        data = data[2:]
    return str2

class Thread_GetBACNetInfo (threading.Thread):   #继承父类threading.Thread
    def __init__(self, ip, fp_w):
        threading.Thread.__init__(self)
        self.ip = ip
        self.ws = fp_w
        #self.collection = collection
        #self.num = num
        #self.es = es
    def run(self):                   #the function write to run,after create thread, it automatic run itself      
        IP = self.ip
        all_dict = {}
        dictOfBACNetInfo = {}
        
        str_send = '810a001101040005010c0c023FFFFF194b'

        port = 47808
        address = ("", 0)   #选择随机可用的端口
        #TargetAddr = ("223.72.246.194", port)
        TargetAddr = (IP, port)    
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        s.bind(address)
        #s.connect(TargetAddr)
        orig_query = dataSwitch(str_send)
        print orig_query
        s.sendto('', TargetAddr)     #先发送一次空字符串，类似测试通路的功能
        #s.sendto('',TargetAddr)
        s.sendto(orig_query, TargetAddr)
        #print s
        
        s.settimeout(5)
        #result_IP = ''
        #time.sleep(3)
        try:
            data,ADDR = s.recvfrom(BUFSIZE)
            if data:
                print repr(data)
            #print ADDR
            time.sleep(1)
            if data.startswith('\x81',0,3): #响应以0x81起始，说明是BACNet,写入相关文件中
                print 'Discover BACNet successfully'
                
                
                try:
                    dictOfBACNetInfo = BACNetlib2.GetInfo(TargetAddr, s, data)
                except Exception,e:
                    dictOfBACNetInfo['error'] = str(IP + ' ') + str(e)
                    with open('bacnet-error.txt','a') as fp_error:
                        fp_error.write(IP+'\n')
                
                s.close()
                
                mylock.acquire() #Get the lock
                with open('result_BACNet_only_ip.txt','a') as fp_w:
                    fp_w.write(IP + '\n')                
                
                #self.ws.write(IP+'\n')
                #self.ws.flush()
                mylock.release()  #Release the lock.              
            
            
        except Exception,e:
            print 'recvfrom error', e
            s.close()
        
        
        current_time = time.strftime(ISOTIMEFORMAT, time.localtime())
        print current_time         
        all_dict["IP"] =  IP
        all_dict["created_time"] = current_time  
        all_dict["BACNet"] = dictOfBACNetInfo
        
        mylock.acquire() #Get the lock         
        self.ws.write(str(all_dict) + '\n')
        mylock.release()  #Release the lock.
        
        del dictOfBACNetInfo
        del all_dict          

def scan(taskName, fileNeedScan):
    """
        if len(sys.argv) != 5:
            print 'I need 5 arguments'
            sys.exit()
        shortargs = 't:f:'
        opts,args = getopt.getopt(sys.argv[1:], shortargs)
        for opt,value in opts:
            if opt == '-t':
                print 'ThreadNum is ',value
                ThreadNum = int(value)
            elif opt == '-f':
                print 'file is',value
                fileNeedScan = value
    """    
    ThreadNum = 10
    print 'xx', fileNeedScan
    fp_r = file(fileNeedScan,'rb')
    
    #fp_time = file('CostTime.txt', 'w')

    current_time = time.strftime(ISOTIMEFORMAT, time.localtime())
    print current_time
    #print time.time()
    if not os.path.exists('.\\result'):
        os.mkdir('.\\result')
    
    file_result = '.\\result\\BACNet_' + taskName + current_time.replace(':', '_') + '.txt'
    fp_w = file(file_result, 'wb')
    
    #fp_time.write(str(current_time)+'\n')
    starttime = time.time()
    
    #line_num = 0
    #ip_list = []
    threads = []
    
    while 1:
        line = fp_r.readline()
        #lines = fp.readlines()
        #line = line.strip()
        if not line:           
            break
        #global line_string
        line_string = line.strip()
        print "current_line====", line_string
        list_line = line_string.split("-")

        #ipadrs = line_string.split("\t")
        #print len(ipadr)
        
        #IP('192.168.1.0/29').strNormal(3)
        
        small_address = ip2long(list_line[0])   #存储小的ip地址的整数
        large_address = ip2long(list_line[1])   #存储大的ip地址的整数        
        
        
        for ip_long in range(small_address,large_address+1):
            
            ip = long2ip(ip_long)
            print "current process ip:", str(ip)        
            
            while 1:
                if (threading.active_count() < ThreadNum):

                    current_thread = Thread_GetBACNetInfo(str(ip), fp_w)
                    current_thread.setDaemon(True)
                    try:
                        current_thread.start()
                        time.sleep(0.01)   #每启动1个线程sleep 0.5s，保证线程不要启动过快
                    except Exception, e:
                        print 'start new thread failed:',e
                        time.sleep(3)
                    else:
                        threads.append(current_thread)
                        break   #start new thread success! break current cycle, read the next ip
                else:
                    time.sleep(1)
            
    while 1:
        alive = False
        for i in range(len(threads)):
            alive = alive or threads[i].isAlive()   #判断所有子线程是否完成
        if not alive:
            break
   
   
   
    current_time = time.strftime(ISOTIMEFORMAT, time.localtime())
    print current_time  
    #fp_time.write(str(current_time))
    #fp_time.close()                
    endtime = time.time()
    print 'end:', (endtime - starttime)

    fp_w.close()
    fp_r.close()
    print 'all file processed!'
    print "Exiting Main Thread"
    
if __name__ == "__main__":
    
    
    
    
    scan(sys.argv[0], sys.argv[1])