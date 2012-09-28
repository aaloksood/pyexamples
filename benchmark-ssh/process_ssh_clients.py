#!/usr/bin/env python
import sys
import multiprocessing
import time
import csv
from ast import literal_eval
import datetime
from time import sleep

import socket

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


results_file = 'process_results_%s.csv' % (datetime.datetime.now())
#cmd = 'sleep 10000'
cmd = """for i in $(seq 6);do sleep 5;echo Loop $i;done;echo bye bye;"""


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


def runcmd(host):
    sshhandle = SSHRemoteClient(host, username, password)
    sshhandle.execute(cmd)


def do_the_calculations(numworkers):
    starttime = time.time()
    mythreads = []
    for i in range(numworkers):
        #my_print('starting worker #%s' %i)
        hostname = hostnames[i % len(hostnames)]
        b = multiprocessing.Process(target=runcmd, args=(hostname, ))
        mythreads.append(b)

    [x.start() for x in mythreads]
    
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
                if not besttime or (exectime > besttime):
                    besttime = exectime
            print '%s workers time %s' % (numworkers, besttime)
            csvwriter.writerow([numworkers, besttime])





