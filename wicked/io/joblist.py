#!/usr/bin/env python
# 03.06.2016, noname

# collect a series of jobs and then execute them in one go.

# inherits from superjob

from superjob import *
from collections import deque

class joblist(superjob):
    '''
    write the doc :)
    '''
    def __init__(self,listname,debug=False):
        superjob.__init__(self, name="joblist",debug=debug)
        self.listname=listname
        self.jobs=deque()
        
        #if self.debug:
        #    print "%s init ctd. for '%s'" % (self.name, self.listname)

    def execute(self):
        if self.debug:
            print "execute: joblist '%s'" %(self.listname)
            print "joblist contains %d commands" % len(self.jobs)

        for job in self.jobs:
            if self.debug:
                print job.name
            job.execute()
        
    def addjob(self, jobinstance):
        self.jobs.append(jobinstance)
        
if __name__ == '__main__':
    import renamejob,lhajob,copyjob,dmsjob,zipjob
    l=joblist("example list",True)
    
    # testing all commands
    f=open("t:/rename_source.txt","wb")
    f.write("hjkashd")
    f.close()
    
    l.addjob(renamejob.rename("t:/rename_source.txt","t:/1-renamed.txt",True) )
    l.addjob(copyjob.copy("t:/1-renamed.txt", "t:/2-copied.txt") )
    l.addjob(lhajob.unlha("t:/Turrican.lha","t:/",True) )
    l.addjob(zipjob.unzip("t:/zipjob.zip","t:/",True) )
    l.addjob(dmsjob.undms("t:\SANITY-Arte.dms","t:\Sanity-Arte.adf",True) )
    
    l.execute()
    l.__exit__()