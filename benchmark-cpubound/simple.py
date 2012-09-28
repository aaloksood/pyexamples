#!/usr/bin/env python
import sys
import time

total = int(sys.argv[1])




if __name__ == '__main__':
    starttime = time.time()
    j = total
    while j:
        j = j-1
    
    print 'timetaken = %s' % (time.time() - starttime)

    
