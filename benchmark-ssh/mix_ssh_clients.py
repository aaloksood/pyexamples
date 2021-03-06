#!/usr/bin/env python

import sys
import multiprocessing
from gevent import socket, spawn, sleep, joinall, Greenlet
from gevent.select import select
from gevent import monkey, local
import time
import csv
from ast import literal_eval
import datetime
import libssh2

monkey.patch_all()

DEBUG=False

if len(sys.argv) < 5:
    print """usage: iters username password numworkers_list"""
    sys.exit(1)

iters = int(sys.argv[1])
username = sys.argv[2]
password = sys.argv[3]
mylist = literal_eval(sys.argv[4])
#hostnames = ['localhost']
hostnames = ['10.5.5.214', '10.5.5.121', '10.5.5.172', '10.5.5.180']


numprocs = 4

results_file = 'greenmix_results_%s.csv' % (datetime.datetime.now())
#cmd = 'sleep 10000'
cmd = """for i in $(seq 300);do sleep 0.1;echo Loop $i;done;echo bye bye;"""

def my_print(args):
    if DEBUG: print(args)


def _wait_select(libssh2_sess, sock):
    '''
    Find out from libssh2 if its blocked on read or write and wait accordingly
    Return immediately if libssh2 is not blocked
    '''
    blockdir = libssh2_sess.blockdirections()
    if blockdir == 0:
        return

    readfds = [sock] if (blockdir & 01) else []
    writefds = [sock] if (blockdir & 02) else []
    select(readfds, writefds, [])        
    return

class SSHRemoteClientNonBlocking(Greenlet):
    LIBSSH2_ERROR_EAGAIN= -37
    def __init__(self, hostname, username, password, port=22):
        self.session = None
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(1)
        self.sock.connect_ex((self.hostname, self.port))
        self.sock.setblocking(0)        
        self.session = libssh2.Session()
        self.session.setblocking(0)

        ret = self.session.startup(self.sock)
        while ret==self.LIBSSH2_ERROR_EAGAIN:
            _wait_select(self.session, self.sock)
            ret = self.session.startup(self.sock)

        ret = self.session.userauth_password(self.username, self.password)
        while ret == self.LIBSSH2_ERROR_EAGAIN:
            _wait_select(self.session, self.sock)
            ret = self.session.userauth_password(self.username, self.password)
            
        self.chan = self.session.open_session()
        while self.chan == None:
            _wait_select(self.session, self.sock)
            self.chan = self.session.open_session()

    def execute(self, cmd):
        ret = self.chan.execute(cmd)
        while ret == self.LIBSSH2_ERROR_EAGAIN:
            _wait_select(self.session, self.sock)
            ret = self.chan.execute(cmd)

        while not self.chan.eof():
            _wait_select(self.session, self.sock)
            data1 = self.chan.read_ex()
            while data1[0] > 0:
                #process data
                #print data1[1]
                data1 = self.chan.read_ex()        

        ret = self.session.close()
        while ret == self.LIBSSH2_ERROR_EAGAIN:
            _wait_select(self.session, self.sock)
            ret = self.session.close(cmd)


    def __del__(self):
        if self.session:
            ret = self.session.close()
            while ret == self.LIBSSH2_ERROR_EAGAIN:
                _wait_select(self.session, self.sock)
                ret = self.session.close(cmd)


def runcmd(host):
    sshhandle = SSHRemoteClientNonBlocking(host, username, password)
    sshhandle.execute(cmd)


def do_the_calculations(nworkers):
    mythreads = []
    for i in range(nworkers):
        hostname = hostnames[i % len(hostnames)]
        #print'starting worker #%s' %i
        b = Greenlet(runcmd, hostname)
        b.start()
        mythreads.append(b)

    joinall(mythreads)

    return

if __name__ == '__main__':
    with open('%s' % results_file, 'w') as wfd:
        csvwriter = csv.writer(wfd)
        for numworkers in mylist:
            if numworkers < numprocs:
                numprocs = numworkers
            print 'working on numworkers %s, iterations = %s' % (numworkers, iters)
            besttime = None
            eachprocworkers = numworkers/numprocs
            for x in range(iters):
                starttime = time.time()
                myprocs = []
                for i in range(numprocs):
                    b = multiprocessing.Process(target=do_the_calculations, args=(eachprocworkers,  ))
                    myprocs.append(b)
                    
                [x.start() for x in myprocs]
                [x.join() for x in myprocs]

                endtime=time.time()
                exectime = endtime-starttime
                print 'exectime = %s' % exectime
                if not besttime or (exectime < besttime):
                    besttime = exectime
            print '%s workers time %s' % (numworkers, besttime)
            csvwriter.writerow([numworkers, besttime])

