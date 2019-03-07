#!/usr/bin/env python
import os.path


# build an absolute path from relative path and currentdir
# return: (path, success)
# path is empty if success == False
def raPath(rel, debug=False):
    # get absolute path to current path and normalize relative path
    apath = os.path.abspath(os.curdir)
    rel = os.path.normpath(rel)
    if debug:
        print "raPath: %s %s" % (apath, rel)

    # check special cases "", "." and ".."
    if rel == os.curdir: return apath, True
    if rel == os.pardir:
        h,t = os.path.split(apath)
        if len(t)==0 or len(h)==0:
            return "", False
        return h, True

    # should we go up first?
    h = ""
    if os.pardir != os.sep:
        # hack on 18.11.13 to make work on amiga
        upat = os.pardir
        up = rel.count(upat)
        if up > 0:
            if debug:
                print "going up: %s" % up
            # go up according to rel, chop rel
            h = apath
            for i in range(up):
                h, t = os.path.split(h)
                # remove first occurrence of pat from path (if any)
                pos = rel.find(upat)
                if pos >=0: rel = rel[pos+len(upat):]
                if debug:
                    print rel

    # anything left of rel after this?
    # we are done if not
    if len(rel)==0:
        if os.path.exists(h):
            return h, True
        else:
            return "", False

    # if we reached this, we have to go down into some other path now
    # print "Debug: ", h, rel
    combine = os.path.abspath(h+rel)
    if os.path.exists(combine):
        # print "*** Bamm"
        # print rel, combine
        return combine, True
    else:
        # print "*** Boom"
        # print rel, combine
        return "", False