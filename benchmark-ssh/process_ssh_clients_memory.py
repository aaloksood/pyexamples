#!/usr/bin/env python
import sys
import multiprocessing
import time
import csv

import socket

DEBUG=False

username = sys.argv[1]
password = sys.argv[2]
hostname = 'localhost'

cmd = 'sleep 10000'
#cmd = """for i in $(seq 200);do sleep 0.01;head -10 /etc/passwd;echo Loop $i;done;echo bye bye;"""

def my_print(args):
    if DEBUG: print(args)

class SSHRemoteClient(object):
    def __init__(self, hostname, username, password, port=22):
        import libssh2
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port

        self.session = libssh2.Session()
        self.session.set_banner()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.hostname,self.port))
            self.session.startup(sock)
            my_print(self.session.last_error())
            self.session.userauth_password(self.username,self.password)
            my_print(self.session.last_error())
        except Exception, e:
            print str(e)
            raise Exception, self.session.last_error()

        self.channel = self.session.open_session()
        self.channel.pty()
        my_print(self.session.last_error())

    def execute(self, command="uname -a"):
        buffer = 4096
        rc = self.channel.execute(command)
        my_print(rc)
        while not self.channel.eof():
            data = self.channel.read(buffer)
            if data == '' or data is None: break
            if data:
                my_print(type(data))
                #print data
                pass

        self.channel.close()

    def __del__(self):
        self.session.close()
        my_print(self.session.last_error())


cmd = 'sleep 10000'

def worker_runcmd(num):
    my_print('worker %s starts' % num)
    sshhandle = SSHRemoteClient(hostname, username, password)
    sshhandle.execute(cmd)
    #my_print('worker %s ends' % num)



if __name__ == '__main__':
    counter = 0
    time.sleep(10000)
    for i in range(20):
        for j in range(5):
            b = multiprocessing.Process(target=worker_runcmd, args=(counter, ))
            b.start()
            counter +=1
        print 'Workers started = %s' %counter
        time.sleep(5)
    time.sleep(10000)
