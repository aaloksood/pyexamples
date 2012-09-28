#!/usr/bin/env python

import sys
import psutil

parentid = int(sys.argv[1])

mem = 0
counter = 0

px = psutil.get_pid_list()
for pid in px:
    x = psutil.Process(pid)
    if x.pid == parentid or x.ppid == parentid:
        counter += 1
        mem += x.get_memory_info().rss


print 'mem for %s processes is %s, %s MB' %(counter, mem, (mem/(1024.0*1024.0)))

