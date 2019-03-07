#!/usr/bin/env python
# 03.06.2016, noname

# inherits from superjob

from superjob import *
import shutil
import os

class copy(superjob):
    def __init__(self,fromfile,tofile,debug=False):
        superjob.__init__(self, name="copy",debug=debug)
        self.fromfile=fromfile
        self.tofile=tofile
        #if self.debug:
        #    print "%s init ctd." % self.name

    def execute(self):
        if self.debug:
            print "Copying %s to %s" %(self.fromfile, self.tofile)
        # 1: check if file exists
        if os.path.exists(self.fromfile):
            if os.path.exists(self.tofile):
                if  self.debug:
                    print "warning: destination existed %s" % self.tofile
            shutil.copy(self.fromfile,self.tofile)

        else:
            if  self.debug:
                print "error: nothing to copy at %s" % self.fromfile
        
        # 2: shutil.os.makedirs for target just to be save?

if __name__ == '__main__':
    o=copy("t:/from.txt","t:/to.txt",True)
    o.test()
    o.execute()
    o.__exit__()