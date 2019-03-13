#!/usr/bin/env python
# 04.06.2016, noname

# converts dms to adf file
# based on http://aminet.net/package/misc/unix/undms-1.3.c
# xdms ditched for the time being

# inherits from superjob

from superjob import superjob
import os
import shutil
import wicked.helpers

class undms(superjob):
    def __init__(self,fromfile,tofile,debug=False):
        superjob.__init__(self, name="undms",debug=debug)
        self.fromfile=fromfile
        self.tofile=tofile
        if self.debug:
            print "%s init ctd." % self.name

    def execute(self):
        if self.debug:
            print "execute: undms %s to %s" %(self.fromfile, self.tofile)
            
        # 1: check if fromfile exists
        if os.path.exists(self.fromfile):
            if self.debug:
                pass
            
            # 2: create required dirs
            head,tail = os.path.split(self.tofile)
            if not os.path.exists(head):
                if self.debug:
                    print "undms: need to create directory %s" % head
                shutil.os.makedirs(head)

            # win32, darwin-ppc, amiga, etc
            pstring = wicked.helpers.getPlatformString()

            # 3: undms
            if pstring == "win32":
                cmdline="bin\undms-win32.exe %s %s" % (self.fromfile, self.tofile)
            else:
                cmdline = "./bin/undms-%s %s %s" % (pstring, self.fromfile, self.tofile)

            if self.debug:
                print "undms cmdline: "+cmdline
            os.system(cmdline)
            
        else:
            if  self.debug:
                print "error: disk-image %s does not exist" % (self.fromfile)
        
if __name__ == '__main__':
    o=undms("t:\SANITY-Arte.dms","t:\Sanity-Arte.adf",True)
    o.execute()
    o.__exit__()