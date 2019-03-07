#!/usr/bin/env python
# 04.06.2016, noname

# unarchives zipfile fromfile todir

# inherits from superjob

from superjob import superjob
import zipfile
import os
import shutil

class unzip(superjob):
    def __init__(self,fromfile,todir,onlynames=[], debug=False):
        superjob.__init__(self, name="unzip",debug=debug)
        self.fromfile=fromfile
        self.todir=todir
        self.onlynames=onlynames
        #if self.debug:
        #    print "%s init ctd." % self.name

    def execute(self):
        if self.debug:
            if len(self.onlynames)==0:
                print "execute: unzip %s to %s" %(self.fromfile, self.todir)
            else:
                print "execute: unzip %s to %s (files: %s" % (self.fromfile, self.todir, self.onlynames)
            
        # 1: check if file exists
        if self.fromfile=="t:\\scratch\\Unreal_v1.2_0033.zip":
            pass
        if os.path.exists(self.fromfile):
            if zipfile.is_zipfile(self.fromfile):
                f = zipfile.ZipFile(self.fromfile)
                for name in f.namelist():
                    if name in self.onlynames or len(self.onlynames)==0:
                        destination = os.path.join(self.todir,name)

                        # 2: create required dirs
                        # todo: check if we actually want to create dirs (unzip -jcq didn't)
                        head,tail = os.path.split(destination)
                        if not os.path.exists(head):
                            if self.debug:
                                print "unzip: need to create directory %s" % head
                            shutil.os.makedirs(head)

                        if len(tail)>0:
                            # 3: get binary data
                            content=f.read(name)
                            if self.debug:
                                print "unzip: writing %s (%d bytes)" % (destination,len(content))
                            # 4: save file
                            savefile=open(destination,"wb")
                            savefile.write(content)
                            savefile.close()
        else:
            if  self.debug:
                print "error: archive %s does not exist" % (self.fromfile)
        
if __name__ == '__main__':
    n=unzip("t:/WHDLoad Games Pack U - 2009-05-28.zip","t:/", debug=True)
    n.execute()
    o=unzip("t:/WHDLoad Games Pack U - 2009-05-28.zip","t:/",onlynames=["Unreal_v1.2_0033.zip"], debug=True)
    #Unreal_v1.2_0033.zip
    o.execute()
    o.__exit__()