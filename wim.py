#!python

# !/usr/bin/env python
# 10.10.13 - first test on WHDLoad Installer with BeautifulSoup HTML parsing
# 12.10.13 - v0.02, second version, put into class, cacheGet, build tables from all.html, hasDemo, getMeta
# 13.10.13 - v0.03, made to work on amiga python 2.0 and pc python 2.7, stored local dict, called wimpy
#          - started using komodo ide and debugger
#          - added allv.html, still only demos (games later), added getKnownDemos()
#          - fixed binary download (wb)
#          - added dms support (one disk only, yet)
#          - working on installing the first demo (Not Again) - worked fully automated at 8:53 pm
#          - needs cleanup, make work for other dms prods, control install dirs and other heuristics, track changes?
# 16.10.13 - improved xdms line to use cachedir for saving adf
#          - added getopt -i -l -v
# 17.10.13 - v0.04, realised that Python 2.7.0 at home returns less  results (327 vs 479) with Bs4
#            than Python 2.7.4 at work. time to upgrade I reckon
# 19.10.13 - v0.05, adding parseRefs, bye bye beautiful soup
#          - checks for supported images and types before storing in brain (demos, games, ctros, apps, mags)
#          - renamed getKnownDemos to getKnownEntitites which takes in categories, e.g. games or demos
# 19.10.13 - v0.06, added save format to brain as a dict with "prods" and "stats" etc.
#          - pickle instead of dict
# 20.10.13 - v0.07, added support for corrections.dict which allows providing fixed to the brain-file,
#            e.g. for supplying links (test with Arte and Katakis)
#          - removed functions parseIndexAll, parseIndexAllv
#          - setVariables() for debug and verbose stats, linked to -v option
#          - stats of failure sources in buildimagesmeta. check with "wim.py -rvc"
#          - changed primarykey from str(name) to str((category, basename)), uncovering lots of megademos
#          - improved install do be more clever with searchname matching (e.g. Arte, Sanity_Arte,
#            ('demos', 'Sanity_Arte')) all pass, and Megademo lists matching megademos
#          - made basename and name search lowercase
# 22.10.13 - lowercase search for primary key in install
# 24.10.13 - v0.08, multiple disk install supported (desert dream works)
#          - been ill in bed, working on netbook
#          - v0.09, type switch, added "zip,adf", made Katakis work as the first game (16:43), also R-Type
#          - seperated cache and temp dirs
#          - log errors with references to entityname and added -e option to investigate error occurences
# 25.10.13 - v0.10, been ill in bed, made cracktros work on my netbook 
#          - this involved handling temporary install dir, searching for slaves, and adjusting paths as we go along
#          -- checked all install archives if they come with directory
#             ->>NO (see alienIII, carcharodon, cf, copper, hunt, etc.)
#          - path stuff will be a good base for future additions. a worthy v0.1 :)
# 26.10.13 - v0.11, investigate links before dismissing them in buildImagesMeta, cached via self.brain["nocontent"]
#          - investigateLinkForContent: distinguish between failed connection and no content,
#          -- actually needed a debugger to get all special cases right, documents the function accordingly
#          - saving parsing exceptions/errors to file errors.dict, load back in of needed by -e or -s
#          - tidied up -s output, removed "extension " prefix from those exceptions to facilitate typing
#            (e.g. '-e .lha' vs. '-e "extensions .lha"')
#          - fixed cleanRefsCached so it doesn't loose cached data but only touches "prods" and "stats"
#             -> makes -rc fast again
#          - supported new types ".exe" and ""
#          - added small help
# 01.11.13 - v0.12, added  proof-of-concept for working with zipped install packs, found a route for games/Unreal
# 02.11.13 - v0.2, lhafile and hashing added
#            installing via hash worked with unreal,
#            turrican would work too, but has two slaves, onw for game, the other for install
#            lha line does not work well for hashed install, also afterburner89
#            jaguarxj220 - no hash found a route - support old installs as well
# 09.11.13 - v0.21, getOldInstalls when hashing, searching "old install archives" table on info-page,
#            extracting the lha hrefs from there
# 10.11.13 - added old install archives as list to meta
#          - added hashes for old slaves to meta (should it be tuples with md5 hash?)
# 11.11.13 - slave-filename for go-file now based on what has been installed, rather than what was
#            the name in original install archive (now works with scoopex_megademo, turrican, etc.)
# 18.11.13 - added assigns, special-cased amiga-related bug in raPath
#          - rearranged dirs, now uses tempdir and a "scratch" dir below thar
#          - added managed dir and copied install to there,
#          - creating intermediate dirs like demos/ctros/mags/games on the way
#          - support wildcard matching
# 19.11.13 - skip already installed entitites, made lots of print optional (verbose)
#          - v0.23, changed hashing to use files with base64 url-friendly encode filenames in brain/hashes
# 20.11.13 - v0.3, added remove option, package manager complete
#          - added -f force option, for wildcard install and remove (otherwise overview only)
# 23.11.13 - fixed cacheGet with a cachedir parameter to allow working with other dirs (e.g. temp) as well
#          - (changed Amiga unzip from 5.1d3 to 5.42 - hope this fixes the freezing)
# 23.04.14 - v0.4, started refactoring, populated wicked package
# 21.09.14 - v0.41, started on web ui
# 28.09.14 - added bootstrap.js/.css, started serving responsive index, /prods with sortable table
# // 2 yrs a break
# 04.06.16 - v0.42, started implementing joblist
# 05.06.16 - first installation of Katakis under Windows! (using joblist,unlha,unzip,copy)
# 06.06.16 - switched to PyCharm, fixed unresolved download name, dropped go file
#          - added .dms route, installed Arte
#          - added .adf route, installed 81stTrack_MusicDisk1
# 08.06.16 - fixed unlha, as lhafile munshes filename and comment into filename using "\x00" as seperator
#            (specimen: skidrow swiv ctro)
#          - fixed loadDict/saveDict location mismatch
#          - fixed clean scratch dir on pc
#          - fixed hashing install to work on pc
# 09.06.16 - fixed line encoding in parseRefs which caused the website /prods page to crash
# 15.06.16 - identify installmethods


# todo: clean rawdic install routes
# todo: integrate hashing / hasher2.py
# todo: .lha route
# todo: .lzx route

# probs mit rampage demo: cache hit, da rampage.lha ein game-install ist, und nicht das image der demo
# todo:
#       - add authors to list of issues
#       - load list of names and wildcards from file, merge with existing installbase
#       - make rampage (adf in lha with renaming) work (same for electrons, turricandemo, turrican2demo)
#       - -u update option to inject newer slaves into existing dirs (also rollback?)
# - THE KRYSTAL ausprobieren :)
#
#       - remove should also delete read-only stuff like that mags/alpha*
#       -- os.chmod(path, mode), import stat
#       -- stat.S_IWRITE

#       - -h should not try to install from images first (e.g. megaforce_megademo)
#       - add hashing creator to wim
#       - integrate hash bulding into building index (-bh options)

#       - progress-bar in window title on Amiga?
#       - decide on dict/pickle/zip storage mechanism for hashes

#       - make work with http://aminet.net/package/util/wb/whdautolaunch
#       - move getoldinstalls to parseInfo / getMeta?

#      b- consider http://trac.edgewall.org/wiki/PySqlite instead of dict for speed 

#      b- autodetect rawdic/dic install (find "(set #program "DIC")" , or "(set #program "RawDIC")" in install)
#        -- hinge of set #version in standard whdload install script
#          (dic 2, rawdic 0, patcher 1, files 3, cd 4,  single file 5, arcadia 6)
#        -- set #multiple-versions = "" for the moment, otherwise throw exceptions  
#        -- APPNAME hidden in installer.info (filename may vary) / needed?
#        - stats per entityname on version, multiple-version, etc
#        - procedure P_MakeImages verwendet version als switch - ist sie immer gleich?
#        -- name der images wird in ci_diskname gebaut, dann wird P_CreateImage aufgerufen
#        - umbennungen, u.a. cocacolademo in newname und #sf_new_filename
#        --> install script parser in python wird benoetigt !
#        - P_CopySlave mit %s und #icon_slave
#        - #dest

# check extension, wayfarer, dos, origin, odyssey
#       - play around with xfddecrunch and one of the unsupported demos, maybe try an installer first?

#        -- locate install script in archive/extrated dir
#        -- reuse that code to locate *.inf for renaming to *.info        

#       - make sure chuck rock and the other games disappear from list

#       - investigatelinkforcontent or buildimagesmeta:
#         analyse first four bytes for amiga exe header 000003f3 when extension is ""

#       - make adf work
#       - check why "pixel nation" does not install with adf (got html response instead of dms in cache!)

#       - rename #?.inf #?.info in Python or AmigaOS?
#       - -x for execute option
#       - parse allow in parserefscached from -a option

#      b- modify rawdic to work as command-line tool
#       - switch to allow using standard install-script (yuk)

#       - seperate function for building stats
#       - fix stats upon recreation

#       - fix error line 723 in cleanRefsCached (self.dh.countToDict(self.errors,"removed for missing images '%s'"
#         % self.brain["prods"][name]["images"]))
#       - make lha work
#       - make lzx work
#       - add -f find or finger option like -i but no actions
#       - provide means to investigate/list productions of a certain type


#      b- write tool to facilitate editing the corrections
#       -- could just be slurping correct urls and copyas, and then somehow process that into the stream of data?


#      b- package up by integrating with dcd tools, go-parser, menu, etc.


#       - devise way to deal with broken downloads 
#       - investigate python lha depacking
#         (e.g. http://trac.neotitans.net/wiki/lhafile or http://code.google.com/p/python-libarchive/)
#       -- lhafile install: SET VS90COMNTOOLS=%VS100COMNTOOLS%,
#          easy_install http://svn.neotitans.net/lhafile/ works on pc!
#       - investigate compile / freeze options, as in http://effbot.org/zone/python-compile.htm

#       - use md5 hashes to help verify / install the right software
#         (lha, lzx, rawdic, dic, patcher, installer, xfdmaster quite a list :)

# interesting specimen to evolve wim
# pychedelic: has comma seperated direct links to lha data!
# rampage: is "adf in lha" http://aminet.net/pub/aminet/demo/track/Rampage.lha
# devils' key: 3 disk 6 dms does not work, found 3 disk 3 dms, still doesnt work although it is dic
# s (skarla 40k intro): exe not accepted by slave (wrong file, packed?)
# musical rabbit needs unpacking (xfd :)
# big business: absolute decrunching not supported / wrong file
# capitalpunishment, virtual karting: no hash finds a route (v0.21)
# spreadpoint turrican music show (filecopy(5) and dexfd required)

# what bugs me
# -missing delays in hd load demos, e.g. absolute inebriation title pic, rink a dink first pic
# -quitkey code must be given in decimal on commanline (69 instead of $45) on commandline (but not in tooltype)
#  but cli based help (whdload w/o options) list them in hex and w/o preceeding $, e.g. 45. very confusing.

# misc finds:
# immediate blitter option makes old demos look as intendend (exception absoluteine cubes after exploding planet)

import os, sys, getopt
import md5, base64
import shutil

try:
    import cPickle as pickle
except:
    import pickle

# import variables for file system handling
from os import curdir, pardir, sep

import wicked.proxy.whdloadproxy
from wicked.proxy.whdloadproxy import whdloadproxy  # (could lead to an abstract interface beyond whdload)

# from wicked.helpers import dicthelpers,listhelpers

try:
    import lhafile
except:
    pass

# handle 3 key differences between Win32 2.7 and Amiga Python 2.0
config = {}
try:
    if True:
        config["has_boolean"] = True
except:
    True = 1
    False = 0
    config["has_boolean"] = False

try:
    from bs4 import BeautifulSoup
    import re

    config["has_bs4"] = True

except:
    config["has_bs4"] = False

try:
    import urllib

    config["has_urllib"] = True
except:
    config["has_urllib"] = False

if sys.platform == "amiga":
    config["is_amiga"] = True
else:
    config["is_amiga"] = False


def q(cond, on_true, on_false):
    return {True: on_true, False: on_false}[cond is True]


# global options that can be modified via the command line interface
g_debug = False
g_verbose = False

have_b = False
have_c = False
have_l = False
have_r = False
have_s = False
have_i = False
have_e = False
have_h = False
have_f = False
try:
    from bs4 import BeautifulSoup
    import re

    config["has_bs4"] = True

except:
    config["has_bs4"] = False

try:
    import urllib

    config["has_urllib"] = True
except:
    config["has_urllib"] = False

if sys.platform == "amiga":
    config["is_amiga"] = True
else:
    config["is_amiga"] = False


def q(cond, on_true, on_false):
    return {True: on_true, False: on_false}[cond is True]


# build an absolute path from relative path and currentdir
# return: (path, success)
# path is empty if success == False
def raPath(rel, debug=True):
    # get absolute path to current path and normalize relative path
    apath = os.path.abspath(os.curdir)
    rel = os.path.normpath(rel)
    if debug:
        print apath, rel

    # check special cases "", "." and ".."
    if rel == os.curdir: return apath, True
    if rel == os.pardir:
        h, t = os.path.split(apath)
        if len(t) == 0 or len(h) == 0:
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
                # remove first occurence of pat from path (if any)
                pos = rel.find(upat)
                if pos >= 0: rel = rel[pos + len(upat):]
                if debug:
                    print rel

    # anything left of rel after this?
    # we are done if not
    if len(rel) == 0:
        if os.path.exists(h):
            return h, True
        else:
            return "", False

    # if we reached this, we have to go down into some other path now
    # print "Debug: ", h, rel
    combine = os.path.abspath(h + rel)
    if os.path.exists(combine):
        # print "*** Bamm"
        # print rel, combine
        return combine, True
    else:
        # print "*** Boom"
        # print rel, combine
        return "", False


def test(demo, debug=False, verbose=True, hashing=False):
    # has = demos.hasDemo(demo)
    # print "has: %s" % has
    print
    if debug:
        print "%s, %s" % (demo, has)
    # if has:
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)
    # try to install
    demos.install(demo, debug=debug, verbose=verbose, hashing=hashing)


def installWild(demo, debug=False, verbose=True, hashing=False, force=False):
    # implemented wildcard matching for installs as in http://docs.python.org/2/library/fnmatch.html
    print
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)

    if demo.find("*") == -1:
        # no wildcard in searchname
        demos.install(demo, debug=debug, verbose=verbose, hashing=hashing)
    else:
        # with wildcard
        import fnmatch
        entities = demos.brain["prods"].keys()
        matched = []
        for entity in entities:
            if fnmatch.fnmatch(entity, demo):
                # print entity
                # try to install
                matched.append(entity)
        # 
        entities = len(matched)
        print "Matched %s entities with '%s'" % (entities, demo)
        if force:
            count = 1
            for entity in matched:
                sys.stdout.write(
                    "\n---> %s of %s (%.1f %%): " % (count, entities, float(count / float(entities) * 100.0)))
                count = count + 1
                demos.install(entity, debug=False, verbose=False, hashing=hashing)
        else:
            for entity in matched:
                print " %s" % entity
            print "\nSupply -f option if you want to install all this (%s entities)." % entities


def removeWild(demo, debug=False, verbose=True, hashing=False, force=False):
    # attempt to implement wildcard matching for installs as in http://docs.python.org/2/library/fnmatch.html
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)

    if demo.find("*") == -1:
        # no wildcard
        demos.removeinstall(demo, debug=debug, verbose=verbose, hashing=hashing)
    else:
        # with wildcard
        import fnmatch
        entities = demos.brain["prods"].keys()
        matched = []
        for entity in entities:
            if fnmatch.fnmatch(entity, demo):
                # print entity
                ismanaged = demos.isManaged(entity)
                # check if dir exists
                if ismanaged:
                    matched.append(entity)
        # 
        entities = len(matched)
        print "Matched %s entities with '%s'" % (entities, demo)
        if force:
            count = 1
            for entity in matched:
                sys.stdout.write("---> removing %s of %s (%.1f %%): %s .. " % (
                    count, entities, float(count / float(entities) * 100.0), entity))
                count = count + 1
                demos.removeinstall(entity, debug=False, verbose=False, hashing=hashing)
        else:
            for entity in matched:
                print " %s" % entity
            print "\nSupply -f option if you want to remove all this (%s entities)." % entities


def test2():
    self.parseRefsCached()
    self.saveDict()


# ---get the arguments
print "Wim.py v0.42, WHDLoad Install Manager by Noname (08.06.2016)"

optlist, args = getopt.getopt(sys.argv[1:], 'i:vl:bcr:se:hfw')
if len(optlist) == 0:
    print "  automates your WHDLoad installation chores"
    print
    print "Options:"
    print "  -b  build index"
    print "  -c  clean index"
    print "  -s  stats"
    print "  -e  investigate exceptions"
    print "  -v  be verbose (lots of output)"
    print "  -h  hashing"
    print "  -w  web interface (browser)"
    print
    print "  -l: list categories (: means supply argument, e.g. demos,ctros,games)"
    print
    print "  -i: install (: argument could be name, basename, primary key, or wildcard*, see below)"
    print "  -r: remove (: argument could be name, basename, primary key, or wildcard*, see below)"
    print "  -f  force (required to perform wildcard install or remove)"

    print "\nUsage: "
    print "  wim.py -bcs     (build and clean index, show stats to begin with)"
    print "  wim.py -s       (show stats - works great in alternation with -e)"
    print "  wim.py -e .html (show entitites that had an exception while parsing"
    print "                          because they linked to .html instead of actual file"
    print "                          - likewise with other exceptions as of stats)"
    print ""
    print "  wim.py -l demos (list all demos, likewise games, apps, mags, ctros)"
    print "  wim.py -i roots (install the demo Roots - matching on name)"
    print "  wim.py -i sanity_roots (same, but matching on basename)"
    print "  wim.py -i demos/sanity_roots (same, but matching on primary key)"
    # print "  wim.py -i megademo (try this and feel the ambiguity of the word)"
    # print "  wim.py -i digitech_megademo (install Digitech Megademo)"
    # print "  wim.py -i *megademo* (check everything with Megademo in it)"
    # print "  wim.py -fi *megademo* (actually install everything with Megademo in it)"
    # print "  wim.py -fr *megademo* (and remove everything with Megademo in it)"
    # print
    # print "  wim.py -l ctros (list cracktros)"
    # print "  wim.py -i swiv (install SWIV cracktro by Skid Row)"
    # print "  wim.py -l games (list games)"
    # print "  wim.py -i Katakis (install the game Katakis - matching on name)"
    # print "  wim.py -i games/Katakis (same, but matching on primary key)"
    print
    print "Note:"
    print "  wim.py currently only installs to a tempdir in 't:'"
    print "  It cleans that place prior to any install, so no need to do it by hand."
    print "  You don't have to manually cd there and find the right file to start."
    print "  Instead just issue the 'j' command, which auto-starts the last install!"
    # sys.exit()

# print optlist, args

# instantiate
demos = whdloadproxy(config)

for o, a in optlist:
    print o, a

    if o == "-w":
        print " starting web interface"
        have_h = True
        from wicked.ui import web2

        # cb.setContent("Hello Bottle!")
        # web2.setContent("---> Externer Content")

        # 'content', 'nocontent', 'prods', 'stats', 'noconnection'
        # sub dicts are as follows

        # content: - (lists what?)
        # nocontent: - (lists dead lines)
        # prods: - (lists all prods)
        # stats: category, iauthor, vendor
        # noconnection: -

        web2.setBrain(demos.getBrain())
        web2.runwebui()
        sys.exit()

    if o == "-h":
        print " hashing enabled"
        have_h = True

    if o == "-c":
        # print "  cleanRefs()"
        have_c = True
        # demos.cleanRefsCached()

    if o == "-e":
        # print "  error()"
        have_e_a = a
        have_e = True

    if o == "-l":
        # print "  list known %s" % a
        have_l = True
        # demos.getKnownEntities(a)
        # sys.exit()

    if o == "-s":
        have_s = True
    # #print "  list stats" % a
    #    #demos.getStats()
    #    #sys.exit()

    if o == "-v":
        print "  be verbose"
        g_debug = True
        g_verbose = True
        demos.setVariables(debug=g_debug, verbose=g_verbose)

    if o == "-b":
        # print "  build tables"
        have_b = True

        # demos.buildTables(recursive=True)
        # sys.exit()

    if o == "-f":
        have_f = True

    if o == "-i":
        have_i = True
        installname = a

    if o == "-r":
        have_r = True
        removename = a

        #    if o == "-c":
        # print "  capabilities are: 'urllib'-%s, 'bs4'-%s" % (q(config["has_urllib"],"True","False"), q(config["has_bs4"],"True","False"))

# execute actions
errorsloaded = False
if have_b:
    print "\n---> Building Index"
    demos.parseRefsCached(verbose=g_verbose, hashing=have_h)
    # demos.buildTables(recursive=True)
    errorsloaded = True

if have_c:
    if not errorsloaded:
        demos.loadErrors()
    print "\n---> Cleaning Index"
    demos.cleanRefsCached(hashing=have_h)

if have_s:
    if not errorsloaded:
        demos.loadErrors()
    print "\n---> Stats"
    demos.getStats()

if have_e:
    print "\n---> Investigate parsing Exceptions"
    if not errorsloaded:
        demos.loadErrors()
    demos.getError(have_e_a)
    print "Done."
    sys.exit()

if have_l:
    print "\n---> List"
    demos.getKnownEntities(a)
    sys.exit()

if have_i:
    # print "\n---> Installing"
    installWild(installname, debug=False, verbose=False, hashing=have_h, force=have_f)

if have_r:
    removeWild(removename, debug=False, verbose=False, hashing=have_h, force=have_f)

# print demos.brain

# noch nicht unterstuetzt:
# Audio Violation - guter Test for rawdic Datei extrahierung
# Arte - 1 Disk 2 Files, not linked in index
# Chromagic - dms link aus text beschreibung pulen
# Dance Diverse Vol.1, Delirium, most Megademos - error 205
# Digital Complexity - nicht Disk.1 sondern data (und dann fehler)
# Project Techno - Archive Fehler? go kaputt
# The Simpsons - .lha lag nicht im cahcedir

# test("Dizzy Tunes")
# test("Dizzy Tunes 2")
# test("Face Another Day")
# test("Voyage")

'''
works:

Not Again
Antideluvian Sloppy Spectacle
Groovy
Autumn Nights
Bard In A Box
Planet M (demo too fast, not my fault)
Capricorn One
Cherokee
Crayon Shinchan
Deja Vu (demo laeuft mit logo und musik, aber dann kommt nichts)
Earwig
Exage
Innership
Jukebox
Linus
Maximum Velocity
Megablast
# 17.10.13 - reinstalled python at home 2.7.5, got 480 instead of 327 demos now
Roots
Monoxide
'''
