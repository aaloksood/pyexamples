#!/usr/bin/env python
import sys
import gevent
from gevent import monkey
import time
import csv
from ast import literal_eval
from time import sleep

total = int(sys.argv[1])
iters = int(sys.argv[2])
mylist = literal_eval(sys.argv[3])
results_file = 'cpu_green_results.csv'

monkey.patch_all()

def worker_loop((num, workperworker)):
    #print 'worker %s starts' % num
    j = workperworker
    counter = 0
    while j:
        j=j-1
        counter += 1
        if counter == 1000:
            sleep(0.001)
            counter = 0
    #print 'worker %s ends' % num


def do_the_calculations(numworkers, workperworker):
    starttime = time.time()
    mythreads = []
    for i in range(numworkers):
        b = gevent.Greenlet(worker_loop, (i, workperworker))
        mythreads.append(b)
    
    [x.start() for x in mythreads]
    gevent.joinall(mythreads)

    endtime=time.time()
    timetaken = endtime-starttime
    return timetaken


if __name__ == '__main__':
    with open('%s' % results_file, 'w') as wfd:
        csvwriter = csv.writer(wfd)
        for numworkers in mylist:
            print 'working on numworkers %s, iterations = %s' % (numworkers, iters)
            besttime = None
            workperworker = total/numworkers
            for x in range(iters):
                exectime = do_the_calculations(numworkers, workperworker)
                print 'exectime = %s' % exectime
                if not besttime or (exectime < besttime):
                    besttime = exectime
            print '%s workers time %s' % (numworkers, besttime)
            csvwriter.writerow([numworkers, besttime])
