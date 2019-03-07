#!/usr/bin/env python
# 04.06.2016, noname

# inherits from superjob

from superjob import superjob
import shutil
import os

class rename(superjob):
    def __init__(self,fromfile,tofile,debug=False):
        # type: (object, object, object) -> object
        superjob.__init__(self, name="rename",debug=debug)
        self.fromfile=fromfile
        self.tofile=tofile
        if self.debug:
            print "%s init ctd." % self.name

    def execute(self):
        if self.debug:
            print "execute: rename %s to %s" %(self.fromfile, self.tofile)
        
        # 1: check if file exists
        if os.path.exists(self.fromfile):
            try:
                os.rename(self.fromfile,self.tofile)
            except:
                if os.path.exists(self.tofile):
                    if  self.debug:
                        print "warning: destination existed %s" % self.tofile
                shutil.copy(self.fromfile,self.tofile)
                if os.path.isdir(self.fromfile):
                    # remove dir
                    shutil.rmtree(self.fromfile)
                else:
                    # remove file
                    os.remove(self.fromfile)                    

        else:
            if  self.debug:
                print "error: nothing to rename at %s" % self.fromfile
        
        # 2: shutil.os.makedirs for target just to be save?

if __name__ == '__main__':
    # create demo file
    f=open("t:/rename_source.txt","wb")
    f.write("lalelu")
    f.close()
    
    o=rename("t:/rename_source.txt","t:/renamed.txt",True)
    o.test()
    o.execute()
    o.__exit__()