#!/usr/bin/env python
# 04.06.2016, noname

# unarchives lhafile fromfile todir

# inherits from superjob

from superjob import superjob
import lhafile
import os
import shutil

class unlha(superjob):
    def __init__(self,fromfile,todir,debug=False):
        superjob.__init__(self, name="unlha",debug=debug)
        self.fromfile=fromfile
        self.todir=todir
        if self.debug:
            print "%s init ctd." % self.name

    def execute(self):
        if self.debug:
            print "execute: unlha %s to %s" %(self.fromfile, self.todir)

        # 1: check if file exists
        if os.path.exists(self.fromfile):
            if lhafile.is_lhafile(self.fromfile):
                f = lhafile.Lhafile(self.fromfile)
                for name in f.namelist():
                    # need to sanitize savename, as lhafile munshes name and comment into name, seperated by \x00
                    splitmark = name.find("\x00")
                    if splitmark != -1:
                        savename = name[:splitmark]
                        #print savename
                    else:
                        savename=name


                    destination = os.path.join(self.todir,savename)

                    # 2: create required dirs
                    head,tail = os.path.split(destination)
                    if not os.path.exists(head):
                        if self.debug:
                            print "unlha: need to create directory %s" % head
                        shutil.os.makedirs(head)

                    # 3: get binary data
                    #print name
                    head,tail = os.path.split(name)
                    if len(tail)>0:
                        content=f.read(name)        # todo: fix crash on "ProSIAK\"
                        if self.debug:
                            print "unlha: writing %s (%d bytes)" % (destination,len(content))
                        # 4: save file
                        #print destination
                        try:
                            savefile=open(destination,"wb")
                            savefile.write(content)
                            savefile.close()
                        except:
                            pass
        else:
            if  self.debug:
                print "error: archive %s does not exist" % (self.fromfile)


class unlhaSingleFile(superjob):
    def __init__(self, fromfile, filename, savename, debug=False):
        superjob.__init__(self, name="unlhaSingleFile", debug=debug)
        self.fromfile = fromfile
        self.filename = filename
        self.savename = savename
        if self.debug:
            print "%s init ctd." % self.name

    def execute(self):
        if self.debug:
            print "execute: unlhaSingleFile %s from %s to %s" % (self.filename, self.fromfile, self.savename)

        # 1: check if file exists
        if os.path.exists(self.fromfile):
            if lhafile.is_lhafile(self.fromfile):
                f = lhafile.Lhafile(self.fromfile)
                for name in f.namelist():
                    # need to sanitize savename, as lhafile munshes name and comment into name, seperated by \x00
                    splitmark = name.find("\x00")
                    if splitmark != -1:
                        savename = name[:splitmark]
                        # print savename
                    else:
                        savename = name

                    # only unpack the single wanted file
                    if savename == self.filename:
                        destination = self.savename

                        # 2: create required dirs
                        head, tail = os.path.split(destination)
                        if not os.path.exists(head):
                            if self.debug:
                                print "unlhaSingleFile: need to create directory %s" % head
                            shutil.os.makedirs(head)

                        # 3: get binary data
                        # print name
                        head, tail = os.path.split(name)
                        if len(tail) > 0:
                            content = f.read(name)  # todo: fix crash on "ProSIAK\"
                            if self.debug:
                                print "unlhaSingleFile: writing %s (%d bytes)" % (destination, len(content))
                            # 4: save file
                            # print destination
                            try:
                                savefile = open(destination, "wb")
                                savefile.write(content)
                                savefile.close()
                            except:
                                pass
        else:
            if self.debug:
                print "error: archive %s does not exist" % (self.fromfile)


if __name__ == '__main__':
    o=unlha("t:/Turrican.lha","t:/",True)
    o.execute()
    o.__exit__()
    o2 = unlhaSingleFile("t:/Turrican.lha", "Turrican Install\Turrican.Slave", "t:\\test.slave", True)
    o2.execute()
    o2.__exit__()