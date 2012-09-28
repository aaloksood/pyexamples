#!/usr/bin/env python
import sys
import threading
import time
import csv
from ast import literal_eval
import datetime

import socket

DEBUG=True

if len(sys.argv) < 5:
    print """usage: iters username password numworkers_list"""
    sys.exit(1)

iters = int(sys.argv[1])
username = sys.argv[2]
password = sys.argv[3]
mylist = literal_eval(sys.argv[4])
#hostname = ['localhost']
hostnames = ['10.5.5.214', '10.5.5.121', '10.5.5.172', '10.5.5.180']

results_file = 'thread_results_%s.csv' % (datetime.datetime.now())
#cmd = 'sleep 10000'
cmd = """for i in $(seq 3000);do sleep 0.1;echo Loop $i;done;echo bye bye;"""

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
        globallock.acquire()
        self.buffer = 4096
        self.rc = self.channel.execute(command)
        globallock.release()
        while not self.channel.eof():
            globallock.acquire()
            self.data = self.channel.read(self.buffer)
            globallock.release()
            if self.data == '' or self.data is None: 
                break
            if self.data:
                #process data
                pass


        globallock.acquire()
        self.channel.close()
        globallock.release()

    def __del__(self):
        globallock.acquire()
        self.session.close()
        ##my_print(self.session.last_error())
        globallock.release()


def worker_runcmd(host):
    ##my_print('worker %s starts' % num)
    md = threading.local()
    md.sshhandle = SSHRemoteClient(host, username, password)
    md.sshhandle.execute(cmd)
    ##my_print('worker %s ends' % num)


def do_the_calculations(numworkers):
    starttime = time.time()
    mythreads = []
    for i in range(numworkers):
        hostname = hostnames[i % len(hostnames)]
        #my_print('starting worker #%s' %i)
        b = threading.Thread(target=worker_runcmd, args=(hostname, ))
        b.start()
        mythreads.append(b)
    
    for x in mythreads:
        x.join()

    endtime=time.time()
    timetaken = endtime-starttime
    #my_print('timetaken with %s threads %s seconds' % (numworkers, timetaken))
    return timetaken

if __name__ == '__main__':
    with open('%s' % results_file, 'w') as wfd:
        csvwriter = csv.writer(wfd)
        for numworkers in mylist:
            print 'working on numworkers %s, iterations = %s' % (numworkers, iters)
            besttime = None
            for x in range(iters):
                exectime = do_the_calculations(numworkers)
                print 'exectime = %s' % exectime
                if not besttime or (exectime < besttime):
                    besttime = exectime
            print '%s workers time %s' % (numworkers, besttime)
            csvwriter.writerow([numworkers, besttime])

