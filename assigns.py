# amiga style assigns (sorry, had to do it)
# basic implementation
# todo: error checking, multiple paths per assign
# lxo, 03.07.08
# 18.11.13, fixed curdir = os.path.abspath(os.curdir) for amiga
# 24.04.14, fixed for Ubuntu/Linux, needed a basename on parameter b in os.path.join (otherwise choked on Linux ":/")
'''
assigns allow to define virtual drives (assigns) which can be used instead of hardcoded paths.
if for example you would like to refer to a file "e:\myfolder\myfile"
then you could assign "myassign" to refer to "e:\myfolder"
and subsequently load "myfile" from "myassign:myfile"!

this is very handy as you might sooner or later want to move "myfolder" somewhere else
and then you would only need to modify "myassign" to point to the new place, saving you
from modifying all the hardcoded filenames.
assigns are also extremely handy to work between different os's, e.g. windows and *nix

this is inspired by the amiga os, where assigns were a core part of the os
and where it was considered bad style to use absolute paths!

these assigns are not case sensitive (compared in upper case)
'''

import os
g_assigns = {}


def addAssign(assign, path):
    '''
    adds an assign as a synonym for a path
    no error checking, yet
    no multiple paths per assign, yet
    '''
    g_assigns[assign.upper()] = path

def removeAssign(assign):
    if g_assigns.has_key(assign.upper()):
        del g_assigns[assign.upper()]

def assign(filename):
    '''
    tries to replace assigns in the filename
    and returns outputfilename
    '''
    # only one colon allowed
    if filename.count(":") != 1:
        # don't know what to do with it, return as is
        return filename
    # split on colon
    key,rest = filename.split(":")
    key = key+":"
    upperkey=key.upper()
    # look up key in g_assigns and build full filename
    fullfilename=""
    if g_assigns.has_key(upperkey):
        #print upperkey
        #print "before: %s"% filename
        # fixed on 24.4.14, basename was needed on Linux!
        filename = os.path.join(g_assigns[upperkey],os.path.basename(filename.replace(upperkey,"")))
        #print "after: %s"%filename
        # check if after resulted in another assign
        #if filename.count(":") == 0:
        #    print "abspath: %s" %os.path.abspath(filename)       
        #print "***"
    else:
        # no key for this, return as is and stop the recursion
        return filename
    # check for more assigns
    if assign(filename)!=filename:
        return assign(filename)
    return filename


# general setup
curdir = os.path.abspath(os.curdir)
# print "*** INFO: assign 'PROGDIR:' for '%s'" % curdir
addAssign("PROGDIR:", curdir)



if __name__ == "__main__":
    '''
    demo code for platforms with support for current dir (i.e. no Symbian)
    note that assigns also work on symbian, just this democode propably wouldn't
    (since abspath(".") would always return "C:\\")
    '''
    # set up
    curdir = os.path.abspath(os.curdir)
    print curdir
    addAssign("PROGDIR:", curdir)
    addAssign("HERE:", "PROGDIR:")
    print g_assigns
    print
    # test loading a file (ourselve)
    filename = "HERE:assigns.py"
    fullfilename=assign(filename)
    print filename, " -->", fullfilename
    #fullfilename="/.assigns.py"
    file = open(fullfilename)
    s = file.read()
    file.close()
    print
    print "loaded %d bytes from '%s' (was '%s')" % ( len(s) , fullfilename, filename)

    # prove that the assigns can go as well (usually not needed)
    removeAssign("PROGDIR:")
    removeAssign("HERE:")
    print
    print g_assigns
else:
    curdir = os.path.abspath(os.curdir)
    addAssign("PROGDIR:", curdir)
    #print assign("progdir:")