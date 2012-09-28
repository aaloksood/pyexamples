#!/usr/bin/env python
import sys
import multiprocessing
import gevent
from gevent import monkey, sleep
import time
import csv
from ast import literal_eval

supertotal = int(sys.argv[1])
iters = int(sys.argv[2])
mylist = literal_eval(sys.argv[3])
results_file = 'cpu_mix_results.csv'


total = supertotal/6

monkey.patch_all()

def worker_loop((num, workperworker)):
    #print 'worker %s starts' % num
    j = workperworker
    counter = 0
    while j:
        j=j-1
        counter += 1
        if counter == 100:
            sleep(0.001)
            counter = 0


def do_the_calculations(numworkers, workperworker):

    mythreads = []
    for i in range(numworkers):
        b = gevent.Greenlet(worker_loop, (i, workperworker))
        mythreads.append(b)
    
    [x.start() for x in mythreads]
    gevent.joinall(mythreads)

    return


if __name__ == '__main__':
    with open('%s' % results_file, 'w') as wfd:
        csvwriter = csv.writer(wfd)
        for numworkers in mylist:
            print 'working on numworkers %s, iterations = %s' % (numworkers, iters)
            besttime = None
            workperworker = total/numworkers
            for x in range(iters):
                starttime = time.time()
                myprocs = []
                for i in range(6):
                    b = multiprocessing.Process(target=do_the_calculations, args=(numworkers, workperworker, ))
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





