#!/usr/bin/env python

import sys
import multiprocessing
from gevent import socket, spawn, sleep, joinall, Greenlet
from gevent.select import select
from gevent import monkey
import time
import csv
from ast import literal_eval
import datetime
import libssh2

monkey.patch_all()

DEBUG=False

if len(sys.argv) < 3:
    print """usage: username password"""
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]
hostname = 'localhost'


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
                xyz=1
                data1 = self.chan.read_ex()        

    def __del__(self):
        ret = self.session.close()
        while ret == self.LIBSSH2_ERROR_EAGAIN:
            _wait_select(self.session, self.sock)
            ret = self.session.close(cmd)



cmd = 'sleep 10000'

def runcmd():
    sshhandle = SSHRemoteClientNonBlocking(hostname, username, password)
    sshhandle.execute(cmd)


def spawn_ssh_reqs(num):
    for i in range(20):
        b= spawn(runcmd)
        if num == 0:
            c=spawn(runcmd)
        print '%s Started worker %s' % (num, i)
        sleep(10)

if __name__ == '__main__':
    sleep(10)
    for j in range(4):
        b = multiprocessing.Process(target=spawn_ssh_reqs, args=(j, ))
        b.start()

    time.sleep(10000)


