#!/usr/bin/env python
import sys
import threading
import time
import csv
from ast import literal_eval
import datetime

import socket

DEBUG=True

if len(sys.argv) < 3:
    print """usage: username password"""
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]
hostname = 'localhost'

globallock = threading.Lock()

#def my_print(args):
#    if DEBUG: print(args)

class SSHRemoteClient(threading.local):
    def __init__(self, hostname, username, password, port=22):
        import libssh2
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        globallock.acquire()

        self.session = libssh2.Session()
        self.session.set_banner()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.hostname,self.port))
            self.session.startup(self.sock)
            #my_print(self.session.last_error())
            self.session.userauth_password(self.username,self.password)
            #my_print(self.session.last_error())
        except Exception, e:
            print str(e)
            raise Exception, self.session.last_error()

        self.channel = self.session.open_session()
        self.channel.pty()
        #my_print(self.session.last_error())
        globallock.release()

    def execute(self, command="uname -a"):
        self.buffer = 4096
        self.rc = self.channel.execute(command)
        ##my_print(self.rc)
        while not self.channel.eof():
            self.data = self.channel.read(self.buffer)
            #if data == '' or data is None: break
            if self.data:
                ##my_print(type(data))
                print len(self.data)

        globallock.acquire()
        self.channel.close()
        globallock.release()

    def __del__(self):
        globallock.acquire()
        self.session.close()
        ##my_print(self.session.last_error())
        globallock.release()


cmd = 'sleep 10000'

def worker_runcmd(num):
    #my_print('worker %s starts' % num)
    sshhandle = SSHRemoteClient(hostname, username, password)
    sshhandle.execute(cmd)
    #my_print('worker %s ends' % num)



if __name__ == '__main__':
    counter = 0
    for i in range(20):
        for j in range(5):
            b = threading.Thread(target=worker_runcmd, args=(counter, ))
            b.start()
            counter +=1
        print 'Workers started = %s' %counter
        time.sleep(30)
    time.sleep(10000)
