#!python
#!/usr/bin/env python
# 10.10.13 - first test on WHDLoad Installer with BeautifulSoup HTML parsing
# 12.10.13 - v0.02, second version, put into class, cacheGet, build tables from all.html, hasDemo, getMeta
# 13.10.13 - v0.03, made to work on amiga python 2.0 and pc python 2.7, stored local dict, called wimpy
#          - started using komodo ide and debugger
#          - added allv.html, still only demos (games later), added getKnownDemos()
#          - fixed binary download (wb)
#          - added dms support (one disk only, yet)
#          - working on installing the first demo (Not Again) - worked fully automated at 8:53 pm
#          - needs cleanup, make work for other dms prods, control install dirs and other heuristics, keep track of changes?
# 16.10.13 - improved xdms line to use cachedir for saving adf
#          - added getopt -i -l -v
# 17.10.13 - v0.04, realised that Python 2.7.0 at home returns less  results (327 vs 479) with Bs4
#            than Python 2.7.4 at work. time to upgrade I reckon
# 19.10.13 - v0.05, adding parseRefs, bye bye beautiful soup
#          - checks for supported images and types before storing in brain (demos, games, ctros, apps, mags)
#          - renamed getKnownDemos to getKnownEntitites which takes in categories, e.g. games or demos
# 19.10.13 - v0.06, added save format to brain as a dict with "prods" and "stats" etc.
#          - pickle instead of dict
# 20.10.13 - v0.07, added support for corrections.dict which allows providing fixed to the brain-file, e.g. for supplying links (test with Arte and Katakis)
#          - removed functions parseIndexAll, parseIndexAllv
#         - setVariables() for debug and verbose stats, linked to -v option
#          - stats of failure sources in buildimagesmeta. check with "wim.py -rvc"
#          - changed primarykey from str(name) to str((category, basename)), uncovering lots of megademos
#          - improved install do be more clever with searchname matching (e.g. Arte, Sanity_Arte, ('demos', 'Sanity_Arte')) all pass, and Megademo lists matching megademos
#          - made basename and name search lowercase
# 22.10.13 - lowercase search for primary key in install
# 24.10.13 - v0.08, multiple disk install supported (desert dream works)
#          - been ill in bed, working on netbook
#          - v0.09, type switch, added "zip,adf", made Katakis work as the first game (16:43), also R-Type
#          - seperated cache and temp dirs
#          - log errors with references to entityname and added -e option to investigate error occurences
# 25.10.13 - v0.10, been ill in bed, made cracktros work on my netbook 
#          - this involved handling temporary install dir, searching for slaves, and adjusting paths as we go along
#          -- checked all install archives if they come with directory ->>NO (see alienIII, carcharodon, cf, copper, hunt, etc.)
#          - path stuff will be a good base for future additions. a worthy v0.1 :)
# 26.10.13 - v0.11, investigate links before dismissing them in buildImagesMeta, cached via self.brain["nocontent"]
#          - investigateLinkForContent: distinguish between failed connection and no content,
#          -- actually needed a debugger to get all special cases right, documents the function accordingly
#          - saving parsing exceptions/errors to file errors.dict, load back in of needed by -e or -s
#          - tidied up -s output, removed "extension " prefix from those exceptions to facilitate typing (e.g. '-e .lha' vs. '-e "extensions .lha"')
#          - fixed cleanRefsCached so it doesn't loose cached data but only touches "prods" and "stats" -> makes -rc fast again
#          - supported new types ".exe" and ""
#          - added small help
# 01.11.13 - v0.12, added  proof-of-concept for working with zipped install packs, found a route for games/Unreal
# 02.11.13 - v0.2, lhafile and hashing added
#            installing via hash worked with unreal,
#            turrican would work too, but has two slaves, onw for game, the other for install
#            lha line does not work well for hashed install, also afterburner89
#            jaguarxj220 - no hash found a route - support old installs as well
# 09.11.13 - v0.21, getOldInstalls when hashing, searching "old install archives" table on info-page, extracting the lha hrefs from there
# 10.11.13 - added old install archives as list to meta
#          - added hashes for old slaves to meta (should it be tuples with md5 hash?)
# 11.11.13 - slave-filename for go-file now based on what has been installed, rather than what was the name in original install archive (now works with scoopex_megademo, turrican, etc.)
# 18.11.13 - added assigns, special-cased amiga-related bug in raPath
#          - rearranged dirs, now uses tempdir and a "scratch" dir below thar
#          - added managed dir and copied install to there, creating intermediate dirs like demos/ctros/mags/games on the way
#          - support wildcard matching
# 19.11.13 - skip already installed entitites, made lots of print optional (verbose)
#          - v0.23, changed hashing to use files with base64 url-friendly encode filenames in brain/hashes
# 20.11.13 - v0.3, added remove option, package manager complete
#          - added -f force option, for wildcard install and remove (otherwise overview only)
# 23.11.13 - fixed cacheGet with a cachedir parameter to allow working with other dirs (e.g. temp) as well
#          - (changed Amiga unzip from 5.1d3 to 5.42 - hope this fixes the freezing)


# probs mit rampage demo: cache hit, da rampage.lha ein game-install ist, und nicht das image der demo
# todo:
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
#        -- hinge of set #version in standard whdload install script (dic 2, rawdic 0, patcher 1, files 3, cd 4,  single file 5, arcadia 6)
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

#       - investigatelinkforcontent or buildimagesmeta: analyse first four bytes for amiga exe header 000003f3 when extension is ""

#       - make adf work
#       - check why "pixel nation" does not install with adf (got html response instead of dms in cache!)

#       - rename #?.inf #?.info in Python or AmigaOS?
#       - -x for execute option
#       - parse allow in parserefscached from -a option

#      b- modify rawdic to work as command-line tool
#       - switch to allow using standard install-script (yuk)

#       - seperate function for building stats
#       - fix stats upon recreation

#       - fix error line 723 in cleanRefsCached (self.dh.countToDict(self.errors,"removed for missing images '%s'" % self.brain["prods"][name]["images"]))
#       - make lha work
#       - make lzx work
#       - make zip work
#       - add -f find or finger option like -i but no actions
#       - provide means to investigate/list productions of a certain type


#      b- write tool to facilitate editing the corrections
#       -- could just be slurping correct urls and copyas, and then somehow process that into the stream of data?


#      b- package up by integrating with dcd tools, go-parser, menu, etc.


#       - devise way to deal with broken downloads 
#       - investigate python lha depacking (e.g. http://trac.neotitans.net/wiki/lhafile or http://code.google.com/p/python-libarchive/)
#       -- lhafile install: SET VS90COMNTOOLS=%VS100COMNTOOLS%, easy_install http://svn.neotitans.net/lhafile/ works on pc!
#       - investigate compile / freeze options, as in http://effbot.org/zone/python-compile.htm

#       - use md5 hashes to help verify / install the right software (lha, lzx, rawdic, dic, patcher, installer, xfdmaster quite a list :)

# interesting specimen to evolve wim
# pychedelic: has comma seperated direct links to lha data!
# rampage: is "adf in lha" http://aminet.net/pub/aminet/demo/track/Rampage.lha
# devils' key: 3 disk 6 dms does not work, found 3 disk 3 dms, still doesnt work although it is dic
# s (skarla 40k intro): exe not accepted by slave (wrong file, packed?)
# musical rabbit needs unpacking (xfd :)
# big business: absolute decrunching not supported / wrong file
# capitalpunishment, virtual karting: no hash finds a route (v0.21)

# what bugs me
# -missing delays in hd load demos, e.g. absolute inebriation title pic, rink a dink first pic
# -quitkey code must be given in decimal on commanline (69 instead of $45) on commandline (but not in tooltype)
#  but cli based help (whdload w/o options) list them in hex and w/o preceeding $, e.g. 45. very confusing.

# misc finds:
# immediate blitter option makes old demos look as intendend (exception absoluteine cubes after exploding planet)

import os,sys,getopt,time
import md5, base64
try:
    import cPickle as pickle
except:
    import pickle

# import variables for file system handling
from os import curdir, pardir, sep

from lxo_helpers import dicthelpers,listhelpers

try:
    import lhafile
except:
    pass

# handle 3 key differences between Win32 2.7 and Amiga Python 2.0
config = {}
try:
    if True:
        config["has_boolean"]=True
except:
    True= 1
    False = 0
    config["has_boolean"]=False

# global options that can be modified via the command line interface
g_debug=False
g_verbose=False

have_b=False
have_c=False
have_l=False
have_r=False
have_s=False
have_i=False
have_e=False
have_h=False
have_f=False
try:
    from bs4 import BeautifulSoup
    import re
    config["has_bs4"]=True

except:
    config["has_bs4"]=False

import urlparse
try:
    import urllib
    config["has_urllib"]=True
except:
    config["has_urllib"]=False
    
    
if sys.platform=="amiga":
    config["is_amiga"]=True
else:
    config["is_amiga"]=False
    
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
        if up>0:
            if debug:
                print "going up: %s" % up
            # go up according to rel, chop rel
            h = apath
            for i in range(up):
                h,t=os.path.split(h)
                # remove first occurence of pat from path (if any)
                pos = rel.find(upat)
                if pos >=0: rel = rel[pos+len(upat):]
                if debug:
                    print rel

    # anything left of rel after this?
    # we are done if not
    if len(rel)==0:
        if os.path.exists(h):
            return h,True
        else:
            return "",False

    # if we reached this, we have to go down into some other path now
    #print "Debug: ", h, rel
    combine = os.path.abspath(h+rel)
    if os.path.exists(combine):
        #print "*** Bamm"
        #print rel, combine
        return combine, True
    else:
        #print "*** Boom"
        #print rel, combine
        return "", False

from assigns import *

class whdloadProxy:

    #url_all= "http://www.whdload.de/demos/all.html"
    #url_allv = "http://www.whdload.de/demos/allv.html"
    #url_path = "http://www.whdload.de/demos/" # deprecated since 0.04

    url_whdload = "http://www.whdload.de/"
    url_refs = "http://whdload.de/db/refs.txt"
    placeholder={}

    cachedir = "cache"
    #amidisk = "ff0:"
    tempdir = "progdir:temp"
    systdir = "t:"
    manageddir = "progdir:managed"
    isAmiga = -1
    
    lastt = None
    
    #prods = {}  # results will go here
    brain = {}  # results will go here
    dh=None
    
    debug=False
    verbose=False
    errors={}
    #hashes={} # !!!
    
    # needed to finding the slave in a subdir after unpacking slave lha
    slavesfound=[]
    
    def __init__(self):
        t1=time.clock()
        self.dh=dicthelpers()
        self.lh=listhelpers()
        if self.checkConfig():
            # cant currently build on Amiga Python 2.0
            #self.buildTables(recursive=False)
            #self.saveDict()
            self.loadDict()
            pass
        else:
            self.loadDict()
        t2=time.clock()
        print "done in %.2f seconds." % (t2-t1)
        
        # create t: replacement if not on Amiga
        if not os.path.isdir(assign(self.systdir)):
            self.systdir=self.tempdir
            print "Not running on Amiga, assign t: to /tempdir"

    def setVariables(self, debug=False, verbose=False):
        '''
        external interface for internal state variables
        '''
        self.debug=debug
        self.verbose=verbose
    
    def checkConfig(self, verbose=False):
        '''
        Checks if platform can run buildtables with Bs4 (eg win32), or not (amiga)
        Returns True if it can, otherwise False
        '''
        vi = sys.version_info
        major = vi[0]
        minor = vi[1]
        micro = vi[2]
        platform = sys.platform.capitalize()

        #print "Running Python v%d.%d.%d on %s - %s" % (major,minor,micro,platform,sys.version)
        #print "  capabilities are: 'urllib'-%s, 'bs4'-%s, 'amiga'-%s" % (q(config["has_urllib"],"True","False"), q(config["has_bs4"],"True","False"), q(config["is_amiga"],"True","False"))
        print "  running on Python v%d.%d.%d on %s" % (major,minor,micro,platform)
        
        # check bs4 requirements
        # http://www.crummy.com/software/BeautifulSoup/ -> Beautiful Soup 4 works on both Python 2 (2.6+) and Python 3.
        okversion=False
        if major>=2:
            if major==2 and minor>=6:
                #2.6+
                okversion=True
            elif major==3:
                okversion=True
            
        # check bs4 availability 
        if okversion:
            #todo, maybe
            pass
        
        print        
        if okversion:
            #print "--> generator functionality (scrape website, build tables)"
            self.isAmiga=False
        else:
            #print "--> installer functionality (install)"
            self.isAmiga=True
            
        sys.stdout.write("Initializing ... ")

        return okversion
        
    def saveDict(self):
        self.dh.saveDictionary(repr(self.brain),"brain.dict")
        #print "***PICKLING"
        filehandle = open("brain.pickle","wb")
        pickle.dump(self.brain, filehandle)
        filehandle.close()
        
        # save good content to seperate file to save time upon rebuilding
        if not self.brain.has_key("content"):
            self.brain["content"]={}
        self.dh.saveDictionary(repr(self.brain["content"]),"brain-content.dict")

        # save errors to seperate file to facilitate reading amd save time when not needed, i.e. on Amiga when not using -s or -e
        self.dh.saveDictionary(repr(self.errors),"errors.dict")


        return
    
#!!!
#    def loadHashes(self):
#        if self.hashes=={}:
#            try:
#                filehandle = open("brain-hashes.pickle","r")
#                self.hashes = pickle.load(filehandle)
#                filehandle.close()
#            except:
#                self.hashes=self.dh.loadDictionary("brain-hashes.dict")
#            #self.dh.saveDictionary(self.hashes,"brain-hashes.dict")
#        print " loaded %s hashes\n" % len(self.hashes)
        
    def loadDict(self):
        #self.prods=eval(self.dh.loadDictionary("brain.dict"))
        try:
            filehandle = open("brain.pickle","r")
            self.brain = pickle.load(filehandle)
            filehandle.close()
        except:
            self.brain={}
            self.brain["prods"]={}
            self.brain["stats"]={}
            #dicts for stats, filled by parseRefs, reachable from getStats()
            self.brain["stats"]["category"]={}
            self.brain["stats"]["vendor"]={}
            self.brain["stats"]["iauthor"]={}
            # needed by buildImagesMeta to keep track of links that have no content-length (i.e. dirs)
            self.brain["nocontent"]={}
            self.brain["content"]={}
        try:
            self.brain["content"]=eval(dh.loadDictionary("brain-content.dict"))
        except:
            #print "*** Error: Can't load 'prods.dict'. Run this on Windows first!"
            pass

        # make sure to have dicts in place        
        if not self.brain.has_key("content"):
            self.brain["content"]={}
        if not self.brain.has_key("nocontent"):
            self.brain["nocontent"]={}
        if not self.brain.has_key("noconnection"):
            self.brain["noconnection"]={}

    def loadErrors(self):
        '''
        load errors from file, in case user wants to investigate them, e.g. -s or -e option
        '''
        self.errors=eval(self.dh.loadDictionary("errors.dict"))
        
    def cacheGet(self, url, cachedir=cachedir):
        '''
        Gets content from a URL and drops a copy in cachedir. Will use content from the cached file from then on.
        
        Limitations:
        - Currently does not handle multiple basenames from different URLs
        
        Returns a string
        '''
               
        # get basename (last component) and construct local filename
        basename = os.path.basename(url)
        filename = os.path.join(cachedir,basename)
        
        # strategy 1: try getting a cached copy and return
        if os.path.exists(filename):
            # open the existing file
            file=open(filename)
            if file:
                content = file.read()
                file.close()
                return content
            
        # strategy 2: try getting the url, drop a cached binary copy, and return the content
        try:
            content = urllib.urlopen(url).read()
            savefile = open(filename, "wb")
            savefile.write(content)
            savefile.close()
        except:
            content=""
                
        return content    
    
    def expandPlaceholders(self, url, debug=False):
        '''
        uses self.placeholder to expand url to original state
        '''
        if url=="http://ftp.amigascne.org/pub/amiga/Groups/B/Bastards":
            pass
        
        #print url
        if url.startswith("http"):
            # no expansion needed
            return url
        if url.startswith("ftp"):
            # no expansion needed
            return url
        
        elem = url.split(":")
        if len(elem)!=2:
            # don't know
            if debug:
                print "*** Warning: placeholder error with: %s (%s)" % (url,str(elem))
            return url
        
        '''
        url="aminet:demo/aga/sanity_roots.dms"
        {'aminet': 'http://www.aminet.net/'}
        
        '''
        # substitute placeholder
        if self.placeholder.has_key(elem[0]):
            #print elem[0], elem[1]
            return self.placeholder[elem[0]]+elem[1]
        # otherwise just return input
        return url
        
    def investigateLinkForContent(self, url, debug=True,verbose=False):
        '''
        check for binary content at url
        this is the last resort when there was no proper data with known extension linked
        it basically distiguishes between websites and binary (in Amiga format, should add that)
        see the documented steps in the code
        
        returns two variables: success, connection
        - success is True upon success, i.e. Amiga binary content found, otherwise False
        - connection is True when there was a connection to the url or false if there was a connection error
        '''

        # false positive on "ftp://ftp.amigascne.org/pub/amiga/Groups/U/United_Forces/UFO-Sensenmann" and many other
        #if url=="ftp://ftp.amigascne.org/pub/amiga/Groups/U/United_Forces/UFO-Sensenmann":
        #if url=="http://ftp.amigascne.org/pub/amiga/Groups/B/Bastards":
        #    print "*** Info: hard coded breakpoint"
        #    #return True

        # step 1 - check if we had been here before and take shortcut if we have
        # there are many repetitive links in whdload data, e.g. ftp://ftp.funet.fi/pub/amiga/demos/Silents (dir rather than actual file) 

        if self.brain["nocontent"].has_key(url):
            if verbose:
                print "%s - * NO CONTENT (cached) *" % url 
            return False,True   # no content, connection ok (cached)

        if self.brain["noconnection"].has_key(url):
            if verbose:
                print "%s - * NO CONNECTION (cached) *" % url 
            return False,False   # no content, connection ok (cached)

        if verbose:
            sys.stdout.write ("\n*** Info: Investigating '%s' .. " % (url))

        # step 2 - open the url for inspection, get headers into d
        try:
            h=urllib.urlopen(url)
            d=h.headers.dict
            if d.has_key("content-length"):
                cl=d["content-length"]
                ct=""
                if d.has_key("content-type"):
                    ct=d["content-type"]
                if verbose:
                    sys.stdout.write("length: '%s', \ntype: '%s'\n" % (cl,ct) )
                    print d
                
                
                # step 2.1 - reject common website content-types, i.e. if the whdload hint points to a website rather than the desired file 

                # http://ftp.amigascne.org/pub/amiga/Groups/F/Flash_Productions returns type: 'text/html; charset=iso-8859-1'
                # most other servers did return type: 'text/html;charset=iso-8859-1' (no space after ;)
                # briefly considered ct.startswith("text"), but this was too aggressive and generated false positives!
                if ct.startswith("text/html") and ct.find("charset=iso-8859-1"):
                    self.dh.countToDict(self.brain["nocontent"], url)
                    if verbose:
                        print "*** Conclusion: No content in data, i.e. not binary (this is a website) *"
                        # print self.brain["nocontent"][url] # print counter of occurences
                    return False, True  # no content, connection ok (cached)
            else:
                # step 2.2 - reject empty content
                
                # no content-length
                self.dh.countToDict(self.brain["nocontent"], url)
                if verbose:
                    print "*** Conclusion: No content as content-length is 0"
                    # print self.brain["nocontent"][url] # print counter of occurences
                return False, True  # no content, connection ok (cached)
        except:
            # step 3 - take care of failed connections
            self.dh.countToDict(self.brain["noconnection"], url)
            if verbose:
                print "Failed Connection\n*** Conclusion: None (due to connection failure)"
                # print self.brain["noconnection"][url] # print counter of occurences
            return False, False # no content, connection FAILED
        
        
        # step 4 - passed all tests, should be okay so far, done
        print "***Info: Accepted as 'content': %s\n" % url
        self.dh.countToDict(self.brain["content"], url)
        # also double-log to errors, to make it browsable via the -e option
        #self.dh.countToDict(self.brain["content"], url)
        self.dh.logValueToDict(self.errors,"content", url)
        return True, True # content ok, connection ok! (we want more of this :)
        
    def buildImagesMeta(self, prodname, hint, debug=False, verbose=False, allow=[".dms",".adf","", ".exe", ".lha"], primary=None):
        '''
        consume non deterministic pointer to images and try to be clever about it
        input: last entry from the line from the list of installs
        out dictionary with 
        '''
        # quick out if images is already a dict not a str
        if type(hint)=="dict":
            return hint # means that it was most probably already fixed or corrected
  
        # if primary is given use that for logging errors
        if primary != None: 
            errorname = primary
        else:
            errorname = prodname
        
        # expand hint using placeholder
        # e.g. amigascne: -> http://ftp.amigascne.org/pub/amiga/Groups/
        hintfull = self.expandPlaceholders(hint)
        
        #if demo=="Roots":
        #if hint=="ftp://ftp.amigascne.org/pub/amiga/Groups/U/United_Forces/UFO-Sensenmann": # done - added allowed extension ""
        #if hintfull=="http://ftp.amigascne.org/pub/amiga/Groups/C/Channel_42":
        
        #if hintfull=="http://ftp.amigascne.org/pub/amiga/Groups/B/Bastards":
        #    print "*** Info: caught specimen"

        # define for safety
        content=False
        connection=False
        lateaccept=False    # will be true if investigatelink confirmed content in hintfull, e.g. animotion

        if True:
            #print "--> parsing image locations"
            # one disks first, start with dms
            
            # get basename
            
            # todo: geturl fuer php endungen
            
            seenat, filename = os.path.split(hintfull)
            #seenat = self.expandPlaceholders(seenat) # done above
            if len(filename)==0:
                # at this point it is unclear if we have a file (no known extension, could also be a directory)
                # (e.g. ftp://ftp.amigascne.org/pub/amiga/Groups/P/Phenomena/PHENOMENA-Animotion)
                # therefore investigate the link in seenat
                if len(seenat)>0:
                    if debug:
                        sys.stdout.write ("\n%s, " % (prodname))
                    content,connection=self.investigateLinkForContent(seenat, debug=debug, verbose=verbose)
                    if not content and connection:
                        self.dh.logValueToDict(self.errors,"nocontent", errorname)
                        return {}
                    elif not connection:
                        if verbose:
                            print "*** Warning: connection error - skipping"
                        #print self.brain["noconnection"][seenat]   # print counter of occurences 

                else:
                    # empty hint
                    self.dh.logValueToDict(self.errors,"emptyhint", errorname)
                    if verbose:
                        print "*** Warning: no direct link to: %s (%s)" % (prodname,hint)
                    return {}
            
            # get suffix
            trash, ext = os.path.splitext(hintfull)
            ext=ext.lower()

            if len(ext)==0:
                # at this point it is unclear if we have a file (no known extension, could also be a directory)
                # (e.g. ftp://ftp.amigascne.org/pub/amiga/Groups/P/Phenomena/PHENOMENA-Animotion)
                # therefore investigate the link in hint/hintfull
                if len(hintfull)>0:
                    if debug:
                        sys.stdout.write ("\n%s, " % (prodname))
                    #hinturl=self.expandPlaceholders(hint) # done above
                    if not self.brain["content"].has_key(hintfull):
                        content,connection=self.investigateLinkForContent(hintfull, debug=debug, verbose=verbose)
                        if not content and connection:
                            self.dh.logValueToDict(self.errors,"nocontent", errorname)
                            return {}
                        elif not connection:
                            if verbose:
                                print "*** Warning: connection error - skipping"
                            # print self.brain["noconnection"][hintfull]    # print counter of occurences
                        # last check: hint must not end on "/" otherwise it cannot be a file
                        if not hintfull.endswith("/"):
                            lateaccept=True # now this should be usable content that just had no extension
                else:
                    # empty hint
                    self.dh.logValueToDict(self.errors,"empty hint", errorname)
                    if verbose:
                        print "*** Warning: no direct link to: %s (%s)" % (prodname,hinturl)
                    return {}
            
                # my hinge is that this would be demos from the content dict like animotion
                if ext=="" and lateaccept:
                    pass    #print "breakpoint"
            
            # check for allowed extensions
            if ext not in allow:
                self.dh.logValueToDict(self.errors,"%s" % ext, errorname)
                if verbose:
                    print "*** Warning: unsupported extension '%s' for '%s' ('%s','%s')" % (ext,prodname,hint,seenat)
                return {}
            if debug:
                print prodname, seenat, filename, ext
            
            #print "still here"
            
            # pack it up
            diskimages = {}
            disk = []   # list because there could be several images per disk (dms frequently 2 per disk)
            image = {}
            image["file"]=filename
            image["seenat"]=seenat
            image["type"]=ext # reconsider after adding the other types
            
            disk.append(image)
            diskimages[1]=disk
         
            return diskimages
        else:
            return {}
        
        
    def parseInfo(self, demoname, debug= True):
        '''
        Parses info page of prod demoname upon request
        '''
        if config["has_bs4"]==False:
            return
        #s = self.cacheGet(self.url_path + self.brain["prods"][demoname]["infox"])
        s = self.cacheGet(self.url_whdload + self.brain["prods"][demoname]["category"] +self.brain["prods"][demoname]["info"])
        # parse html

        if debug:
            string =  "Parsing info for '%s' .. " % (demoname)
            sys.stdout.write(string)
        else:
            #sys.stdout.write(".")
            pass
                
        w = BeautifulSoup(s)
        
        if debug:
            print w
        
            print "*** End info"
        
        # collect table rows
        #tr= w.find_all("tr")
        #print "found %d entries" % (len(tr))
        
        # mark as done
        self.brain["prods"][demoname]["infoparsed"]=True
        return
    
    def hasDemo(self, demoname):
        '''
        Return True if demoname is known
        '''
        return self.brain["prods"].has_key(demoname)
    
    def getMeta(self, demoname, debug=False):
        if self.hasDemo(demoname):
            if self.brain["prods"][demoname]["infoparsed"]==False:
                # get details
                self.parseInfo(demoname, debug)
            return self.brain["prods"][demoname]
        else:
            return None
    
    def getKnownEntities(self,category):
        '''
        prints all currently known and supported entitites of a certain category. prints all if category is ""
        '''
        if category=="":
            p=True
        else:
            p=False
        for prod in self.brain["prods"].keys():
            if p or self.brain["prods"][prod]["category"]==category:
                entity=self.brain["prods"][prod]
                #print entity
                images = entity["images"]
                if images !=None:
                    numdisks = len(images)
                else:
                    numdisks = "No"
                print "%s by %s (%s - %s disks)" % (entity["prodname"], entity["vendor"], entity["basename"], numdisks )
                #print "%s by %s (type s)" % (entity["prodname"], entity["vendor"])
        if category not in self.brain["stats"]["category"].keys():
            sys.stdout.write ("Supplied argument '%s' is no known category." % category)
            print " Consider using one of: %s" % self.brain["stats"]["category"].keys()
    
    def getError(self,error):
        '''
        more details on occurences of error/exceptions
        '''
        if self.errors.has_key(error):
            elems = self.errors[error]
            print "Exception '%s' occured %d times:" % (error, len(elems))
            for elem in elems:
                if self.brain["prods"].has_key(elem):
                    print "  %s, %s" % (elem,self.brain["prods"][elem]["oimages"])
                else:
                    print "  %s, -" % (elem)
                
        else:
            print "*** Warning: no known exception cause '%s'" % error
            print "Did you supply the -r option for reference parsing in case there is no errors.dict file?"
    
    def getStats(self):
        '''
        print some stats from parseRefs

        self.stat_category={}
        self.stat_vendor={}
        self.stat_iauthor={}

        '''
        # 1. computer "uncertainty" list, where links are given but no image has been recognized
        # no direct link, missing images
        #l1=self.errors["no direct link"]
        #l2=self.errors["missing images"]
        #uncertain = self.lh.difference(l1,l2)
        #uncertain = filter(lambda x:x not in l2,l1)
        #uncertain = list(set(l1) and set(l2))
        #uncertain = list(set(l1) - set(ncertain))
        #uncertain = self.lh.difference(self.errors["no direct link"], self.errors["missing images"])
        uncertain=None
        if uncertain != None:
            for elem in uncertain:
                self.dh.logValueToDict(self.errors,"uncertain",elem)
            
        # 2. sort and display results (currently not python v2.0 compatible, i.e. not on Amiga)
        #sorted([('abc', 121),('abc', 231),('abc', 148), ('abc',221)],key=lambda x: x[1])
        #print "Common errors: %s" % str(self.errors.keys())
        print "Known categories: %s" % str(self.brain["stats"]["category"])
        print "\nExceptions while parsing references:"
        tuplelist=[]
        for error in self.errors.keys():
            count = len(self.errors[error])
            tuplelist.append( (error, count) )
        
        # sorted fails on Python 2.0, so just try
        try:
            #pc
            sortedtuplelist=sorted(tuplelist,key=lambda x: x[1])
            for tuple in sortedtuplelist:
                print "  %s : %s" % (tuple[0], tuple[1])
        except:
            #amiga
            for tuple in tuplelist:
                print "  %s : %s" % (tuple[0], tuple[1])
                
        print '\nTip: use -e option to investigate occurences, e.g. -e "nocontent"'
        
    
    def buildTables(self, recursive=False, debug=False):
        '''
        Cache relevant content and parse demo list
        '''
        #self.parseIndexAll(recursive=recursive, debug=False)
        #self.parseIndexAllV(recursive=recursive, debug=False)
        self.parseRefsCached()

    def collection_helper(self, arg, dirname, names, debug=False):
        '''
        os.path.walk helper for findSlaves. look there for more details.
        '''
        counter=0
        if debug:
            print "  dir '%s' has %s files" % (dirname, len(names))
        if dirname.endswith("cache"):
            print "skipping cache"
            return
        for name in names:
            #fullname = dirname+name
            
            propername = os.path.join(dirname, name)
            fullname = propername
            
            #print "dir: '%s', name: '%s', fullname: '%s'" % (dirname,name,fullname)
            #print "dir: '%s', name: '%s', fullname: -" % (dirname,name)
            
            if name.lower().endswith(arg.lower()):
                #fullname = os.path.normpath( dirname + name )
                #fullname = os.path.join(dirname, name)
                #print name
                #print fullname
                #print "isFile: " + fullname + "("+dirname+"  "+name+")"
                self.slavesfound.append(propername)
            #if os.path.isdir(fullname):
            #    #print "isDir: " + fullname + "("+dirname+"  "+name+")"
            #    names.remove(name)
    
    def haveHash(self, md5hash):
        '''
        return True/False if md5hash is known
        '''
        res=False
        #res=self.hashes.has_key(md5hash)
        hashdir = os.path.join("brain","hashes")
        filename = os.path.join(hashdir,md5hash)
        #print filename
        res=os.path.isfile(filename)
        #print res
        return res
   
    def getHash(self, md5hash):
        '''
        return value for key md5hash or None
        '''
        #print "**********"
        if not self.haveHash(md5hash):
            return None
            
        hashdir = os.path.join("brain","hashes")
        filename = os.path.join(hashdir,md5hash)
        #print filename
        s=open(filename).read()
        #print s
        return eval(s)
        
        
    def findHashRoute(self, md5hash, debug=False):
        '''
        try to work out unpack route based on md5hash of this install
        !only works with hashing enabled!
        return list of steps
        '''
        #if not self.hashes.has_key(md5hash):
        if not self.haveHash(md5hash):
            return []

        # step through list of known sightings and find route to top-file
        #listhashes = self.hashes[md5hash] #!!!
        #print "***LEIF"
        listhashes = self.getHash(md5hash)
        #print listhashes
        route=[]
        sight=listhashes[0]
        if debug:
            print listhashes
        while sight["type"]!="f":
            #print sight
            route.append(sight)
            #sightlist=self.hashes[sight["in"]] # !!!
            sightlist=self.getHash(sight["in"])
            #print sightlist
            sight=sightlist[0]
        #print sight
        route.append(sight)
        #print "*** Info: route"
        #print route
        return route
                
    def findSlave(self, dirname, debug=False, hashing=False):
        '''
        WHDLoad Install archives have no fixed directory structure.
        If there is a dir, it might or might not be called like the archive or basename,
        but might also have hd, -hd, -install, etc. attached, or not. 
        Also there might be no directory in the archive (e.g. alien3 or carchrodon)
        The only real given is that the slave ends in .slave. So that is what this function looks for.
        Input> dirname
        Output> fully qualified filename (where slave is contained)
        '''
        # get full absolute path from relative os.curdir 
        (path,success)= raPath(dirname) # needed)
        if not success:
            print "Problem getting absolute path for dirname '%s'.\nStop." %dirname
            print dirname, path, success
            sys.exit()

        searchfor = ".slave"
        if debug:
            print "curdir: '%s', pardir: '%s', sep: '%s'" %(curdir, pardir,sep)
        print "looking for '%s' files in '%s'" % (searchfor, path)

        os.path.walk(dirname, self.collection_helper, searchfor)

        # hacked hashing in here, could be seperated later
        for file in self.slavesfound:
            if hashing:
                if debug:
                    print "%s is file: %s" % (file, os.path.isfile(file))
                #lets hash it
                s=open(file,"rb").read()
                m = md5.new()
                m.update(s)
                
                #md5hash = m.hexdigest()                
                #md5hash= base64.urlsafe_b64encode(m.digest())
                # make urlsafe on amiga without b64encode according to http://pymotw.com/2/base64/
                t1 = base64.encodestring(m.digest())
                t2 = t1.replace("/","_")
                md5hash = t2.replace("+","-")                
                
                if debug:
                    print md5hash
                #print self.hashes[md5hash]["type"]
                self.findHashRoute(md5hash)
                ## step through list of known sightings and find route to top-file
                #listhashes = self.hashes[md5hash]
                ##print listhashes
                #sight=listhashes[0]
                #while sight["type"]!="f":
                #    print sight
                #    route.append(sight)
                #    sightlist=self.hashes[sight["in"]]
                #    #print sightlist
                #    sight=sightlist[0]
                #print sight
                #route.append(sight)
                #print "*** Info: route"
                #print route
                #level=0
                #steps = len(route)
                #print "\n***Info: Found a route with %s steps" % steps
                #for i in range(steps):
                #    step = route.pop()
                #    sys.stdout.write(" "*i)
                #    print step["filename"]
                #print "\n"
            pass
            
        if len(self.slavesfound)==0:
            print "*** Error: no slave found in '%s'\nStop." % dirname
            return
            #sys.exit()
        
        if len(self.slavesfound)>1:
            print "*** Warning: more than one slave found in '%s'. Taking first one.\n%s" % (dirname,self.slavesfound)
        
        file = self.slavesfound[0]
        self.slavesfound=[] # cleanup
        
        # double check it is actually a file
        if not os.path.isfile(file):
            print "*** Error: not a file '%s'\nStop." % file
            sys.exit()
        
        # we are good. lets slice up the result and return the adjusted dir
        print "Found %s" % file
        return file
        
    def findSlaveDir(self, dirname, debug=False, hashing=False):
        '''
        WHDLoad Install archives have no fixed directory structure.
        If there is a dir, it might or might not be called like the archive or basename,
        but might also have hd, -hd, -install, etc. attached, or not. 
        Also there might be no directory in the archive (e.g. alien3 or carchrodon)
        The only real given is that the slave ends in .slave. So that is what this function looks for.
        Input> dirname
        Output> adjusted dirname (where slave is contained)
        '''
        file = self.findSlave(dirname=dirname, debug=debug, hashing=hashing)
        if file!=None:
            head, tail = os.path.split(file)
            return head
        else:
            return None
        
    def isManaged(self, entityname, debug=False):
        '''
        returns True is entityname is managed, i.e. a directory exists
        '''    
        mandir=assign(self.manageddir)
        if debug:
            print mandir
        
        category, basename = entityname.split("/")
        if debug:
            print category, basename

        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir,proddir)
        if debug:
            print proddir, destdir
        if os.path.isdir(destdir):
            return True
        else:
            return False

    def removeinstall(self, searchname, debug=False, verbose=False, hashing=False):
        '''
        remove the entity that matches searchname from manageddir
        '''
        #print searchname
        # find right entity
        # try 1: searchname is (category/basename)
        if self.brain["prods"].has_key(searchname):
            if verbose:
                print "Exact match on primary key: %s" % searchname
            entityname = searchname
        
        else:
            # try : allow capitalization typos, i.e. check lower case
            prodnames=self.brain["prods"].keys()
            foundlower=False
            searchnamelow = searchname.lower()
            for prod in prodnames:
                if searchnamelow==prod.lower():
                    foundlower=True
                    if verbose:
                        print "Match on primary key: %s" % searchname
                    break
            if foundlower:
                entityname=prod
            else:
                # try 3: searchname is basename or name (make sure there is no more than one, as in "Megademo")
                searchnamelow=searchname.lower()
                matched_basenames = []
                matched_names=[]
                for key in self.brain["prods"].keys():
                    prod = self.brain["prods"][key]
                    basename = prod["basename"].lower()
                    name = prod["name"].lower()
                    if searchnamelow==basename:
                        matched_basenames.append(key)
                    if searchnamelow==name:
                        matched_names.append(key)
                # check results
                
                # if 1 matched name, than that is the one
                if len(matched_names)==1:
                    entityname=matched_names[0]
                    if verbose:
                        print "Match on name: %s" % searchname

                elif len(matched_basenames)==1:
                    entityname=matched_basenames[0]
                    if verbose:
                        print "Match on basename: %s" % searchname

                else:
                    print "*** Error: your searchname '%s' yielded no exact match:" % searchname
                    print "on primary key: []"
                    print "on basenames: %s" % matched_basenames
                    print "on names: %s" % matched_names
                    print "Stop.\n"
                    return
                    sys.exit()             
        
        # at this point we know exactly what the user wants, i.e. the entityname
        if debug:
            print entityname

        mandir=assign(self.manageddir)
        if debug:
            print mandir
        
        category, basename = entityname.split("/")
        if debug:
            print category, basename

        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir,proddir)
        if debug:
            print proddir, destdir
        if os.path.isdir(destdir):
            if verbose: 
                sys.stdout.write(" removing '%s' ... " % entityname) #destdir
            import shutil
            shutil.rmtree(destdir, ignore_errors=True)
            print "done."
        else:
            print "Hmm, no dir matched the entityname, what happened?"
        return
            
    def install(self, searchname, debug=False, verbose=False, hashing=False):
        '''
        install a demo, getting all required linked images, etc
        currently works with .dms 1 disk 1 image only
        returns True on success and False otherwise
        '''
        #!!!
        #if hashing and len(self.hashes)==0:
        #    self.loadHashes()
            
        # make a local copy to allow modifications
        installdir = assign(self.systdir)
        
        # we work in our own subdir
        tempwim = "scratch"
        installdir = os.path.join(installdir, tempwim)
        installdir_bak = installdir
        if self.isAmiga:
            if debug:
                print installdir
            if not os.path.isdir(installdir):
                # complain and create it
                if verbose:
                    print "Creating my '%s' directory in %s" % (tempwim,assign(self.tempdir))
                os.makedirs(installdir)
            else:
                # get rid of previous install junk / CAREFULL!!!
                if self.isAmiga:
                    if len(os.listdir(installdir))>0:
                        if verbose:
                            print "Cleaning install-dir '%s'" % installdir
                        os.system('cd %s\ndelete #? all force quiet' % installdir)
                else:
                    if verbose:
                        print "Better not delete %s" % installdir
                    sys.exit()

        # find right entity
        # try 1: searchname is (category/basename)
        if self.brain["prods"].has_key(searchname):
            if verbose:
                print "Exact match on primary key: %s" % searchname
            entityname = searchname
        
        else:
            # try : allow capitalization typos, i.e. check lower case
            prodnames=self.brain["prods"].keys()
            foundlower=False
            searchnamelow = searchname.lower()
            for prod in prodnames:
                if searchnamelow==prod.lower():
                    foundlower=True
                    if verbose:
                        print "Match on primary key: %s" % searchname
                    break
            if foundlower:
                entityname=prod
            else:
                # try 3: searchname is basename or name (make sure there is no more than one, as in "Megademo")
                searchnamelow=searchname.lower()
                matched_basenames = []
                matched_names=[]
                for key in self.brain["prods"].keys():
                    prod = self.brain["prods"][key]
                    basename = prod["basename"].lower()
                    name = prod["name"].lower()
                    if searchnamelow==basename:
                        matched_basenames.append(key)
                    if searchnamelow==name:
                        matched_names.append(key)
                # check results
                
                # if 1 matched name, than that is the one
                if len(matched_names)==1:
                    entityname=matched_names[0]
                    if verbose:
                        print "Match on name: %s" % searchname

                elif len(matched_basenames)==1:
                    entityname=matched_basenames[0]
                    if verbose:
                        print "Match on basename: %s" % searchname

                else:
                    print "*** Error: your searchname '%s' yielded no exact match:" % searchname
                    print "on primary key: []"
                    print "on basenames: %s" % matched_basenames
                    print "on names: %s" % matched_names
                    print "Stop.\n"
                    return
                    sys.exit()             
        
        # at this point we know exactly what the user wants, i.e. the entityname
        data = self.brain["prods"][entityname]
        if verbose:
            print "---> Installing %s by %s (%s)" % (data["name"], data["vendor"], entityname)
            print data
        else:
            #print "%s\n (%s by %s)" % (entityname, data["name"], data["vendor"])
            print "%s" % (entityname)
        
        # check if this entity is already managed, i.e. a directory category/basename exists
        mandir=assign(self.manageddir)
        basename=data["basename"]
        category=data["category"] 
        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir,proddir)
        if os.path.isdir(destdir):
            if verbose:
                print " already exists, skipping"
            return
        
        commands=[] # these will be executed one after another on target system

        # make sure to have metadata
        meta = self.getMeta(entityname)
        #if meta["infoparsed"]!= True:
        #    print "*** Info: no parsed info for this"
        #else:
        #    print "*** Info: Meta: %s" % meta
            
        '''
        {'info': 'Sanity_NotAgain.html', 'prodname': u'Not Again', 'infoparsed': True, 'fromindex': 'all.html', 'groupname':
'?', 'install': 'Sanity_NotAgain.lha',
'images': {1: [{'seenat': 'http://www.aminet.net/demo/mega', 'type': '.dms', 'file': 'notagain.dms'}]}}
'''
        images = data["images"]
        hashes = data["md5"]
        if debug:
            print images
        # number of disks, "ctros" special case as has no images
        try:
            numdisks = len(images)
            if verbose:
                print "Number of disks: %d" % numdisks
        except:
            numdisks = 0
            pass

        # todo: seperate get file from installation handler
    
        # commands batch 1 (Amiga only), unpack installer
        # unpack installer, with special case for "ctros"
        iname = os.path.join(self.cachedir, data["install"])
        # special case for ctros
        if data["category"]=="ctros":
            lhaline = "lha e -N %s %s/" % (iname , installdir)
        else:
            # common case for everything else: try to be clever about it
            #lhaline = "lha e -x0 -N %s #?.inf install #?.slave #?README %s/" % (iname , installdir)
            lhaline = "lha e -N %s %s/" % (iname , installdir)
        commands.append(lhaline)
        if debug:
            print lhaline

        # can only do preparation for this on Amiga
        if self.isAmiga:
            for command in commands:
                os.system(command)
            commands=[]
        
            # find slave, adjust target-dir
            dir=self.findSlaveDir(installdir,hashing=hashing)
            if dir!=installdir:
                if dir==None:
                    return
                print "Adjusting installdir to '%s'" % dir
                installdir = dir
            
        category=data["category"]
        # iterate over disks
        if numdisks>0 or category=="ctros":
            for i in range(numdisks):
                disknum=i+1
                multiimages=False   # True if more than 1 image per disk
                reqimages = len(images[disknum])
                print "Disk %d requires %d images" % (disknum, reqimages)
                if reqimages >1:
                    multiimages = True
                    print "*** Error: Cannot currently handle the case of multiple images per disk"
                    return False
                image = images[disknum][0]
                
                # check for dms
                supportedtypes = (".dms", "zip,adf", ".adf", "", ".exe", ".lha")
                type = image["type"]
                if type not in supportedtypes:
                    print "*** Error: Can currently only handle %s, but this is of type '%s'" % (supportedtypes, type)
                    return False
                print image
                
                # get file
                if debug: 
                    print image["seenat"],image["file"]
                url = image["seenat"]+"/"+image["file"]
                if len(image["file"])==0: # should not be required in the first place, but occured with Faster Than Hell on 18.11.
                    break;
                print "Downloading %s from %s" % (image["file"], url)
                self.cacheGet(url, cachedir=assign(self.tempdir))
                
                # handle dms
                if type==".dms":
                    # un-dms with system call
                    fname = os.path.join(assign(self.tempdir), image["file"])
                    #dmsline = "dms write %s to %s" % (fname, self.amidisk)
                    # http://zakalwe.fi/~shd/foss/xdms/xdms.txt
                    adfname = image["file"].lower().replace(image["type"],".adf")    #lower okay as Amiga filesystem is not case sensitive (error found with "r.o.m. 1" which has upper case .DMS)
                    adfnamefull = os.path.join(assign(self.tempdir), adfname)
                    dmsline = "xdms -d %s u %s +%s" % (assign(self.tempdir), fname,adfname)
                    if debug:
                        print "Creating %s from %s" %(adfnamefull, fname)
                        
                    #os.system(dmsline)
                    #print dmsline
                    commands.append(dmsline)

                    # DIC produces Disk.1/2/3, etc.
                    diskname="Disk.%s" % disknum
                    targetname = "%s" % (os.path.join(installdir,diskname))
                    print targetname
                    copyline = 'copy %s/%s to "%s" ' % (assign(self.tempdir), adfname, targetname)        
                    commands.append(copyline)
                    
                # handle zipped adf
                if type=="zip,adf":
                    fname = os.path.join(self.cachedir, image["file"])
                    adfname = image["image"]
                    adfnamefull = os.path.join(self.cachedir, adfname)
                    # -jo for overwrite -no for keeping
                    unzipline = "unzip -jqo %s %s" % ( "/%s" % (fname) , adfname)
                    # step into tempdir and unzip
                    commands.append("cd %s\n%s" % (assign(self.tempdir),unzipline))
                    # copy adf to installdir
                    # later todo: special case "saveas" for images that need a special name
                    #copyline = 'copy %s/%s to "t:Disk.%s"' %(assign(self.tempdir), adfname, disknum)
                    copyline = 'copy %s/%s to "%s/Disk.%s"' %(assign(self.tempdir), adfname, installdir, disknum)
                    
                    commands.append(copyline)
                
                # handle adf
                if type==".adf":
                    fname = os.path.join(self.cachedir, image["file"])
                    #adfname = image["file"]
                    #adfnamefull = os.path.join(self.cachedir, adfname)
                    # copy adf to installdir
                    # later todo: special case "saveas" for images that need a special name
                    copyline = 'copy %s to "%s/Disk.%s"' %(fname, installdir, disknum)        
                    commands.append(copyline)

                # handle "" and ".exe" (amiga exe that have been downloaded without archive, i.e. also comply to internet url naming)
                if type=="" or type==".exe":
                    fname = os.path.join(self.cachedir, image["file"])
                    copyline = 'copy %s to "%s"' %(fname, installdir)
                    commands.append(copyline)
                    # later todo: special case "saveas" for images that need a special name
                    if image.has_key("copyas"):
                        renameline = 'cd %s\nrename "%s" "%s"' %(installdir, image["file"], image["copyas"])
                        commands.append(renameline)

                # handle lha
                if type==".lha":
                    import lhafile
                    print image
                    lhafilename = os.path.join(assign(self.systdir), image["file"])
                    print lhafilename
                    if lhafile.is_lhafile(lhafilename):
                        f = lhafile.Lhafile(lhafilename)
                        flist = []
                        print " listing %s:" % lhafilename
                        for name in f.namelist():
                            print name



        else:
            #print "*** Info: Data==%s " % data
            route=[]
            if hashing == False:
                if len(hashes)>0:
                    print "*** Info: There is a known hash"
                print "*** Warning: no images found!"
                print "Stop."
                return
                #sys.exit()
            else:
                # try hashing
                print "*** Info: searching via hashes (have %s)" % len(hashes)
                c=1
                foundHashRoute=False
                bestroute=None
                beststeps=1985   # arbitrary high number, lower is better 
                for h in hashes:
                    print "Try hash %s: %s" %(c,h)
                    c=c+1
                    route=self.findHashRoute(h)
                    if len(route)>0:
                        foundHashRoute=True
                        if len(route)<beststeps:
                            beststeps=len(route)
                            bestroute=route
                if not foundHashRoute:                
                    print "*** Warning: no hash found a route"
                    #print "Stop."
                    #sys.exit()
                    return
            # here we have a hash route
            level=0
            steps = len(bestroute)
            print "\n*** Info: Found a route with %s steps" % steps
            for i in range(steps):
                step = bestroute[steps-1-i]
                sys.stdout.write(" "*i)
                print step["fullname"]  # was filename
            # empty unnecessary commands from images method
            commands=[]
            installdir = installdir_bak
            # get rid of previous install junk / CAREFULL!!!
            #if installdir=="t:temp-wim" and self.isAmiga:
            if self.isAmiga:
                if len(os.listdir(installdir))>0:
                    if verbose:
                        print "Cleaning install-dir '%s'" % installdir
                    os.system('cd %s\ndelete #? all force quiet' % installdir)
            else:
                print "\nNot running on Amiga.\nStop."
                #sys.exit()
                return
            if debug: # doppelt mit steps==3
                print bestroute
            # unpack with 3 steps
            arc="archive:kg/packs"  ## hacked - todo
            if steps==3:
                if debug:
                    print bestroute
                zip1=bestroute[2]["fullname"] # pack
                zip2=bestroute[1]["fullname"] # archive
                step3line = "unzip -qo %s %s" % ( '"%s/%s"' % ( (arc,zip1)),  zip2 )
                # step into tempdir and unzip zip from containing pack
                commands.append("cd %s\n%s" % (installdir,step3line) )
                # now unzip the extracted archive
                unzipline = "unzip -qo %s" % ( zip2 )
                commands.append("cd %s\n%s" % (installdir,unzipline) )
            # unpack with 2 steps
            # todo: implement
            
            if not self.isAmiga:
                print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
                print "Stop."
                print commands
                return
            if debug:
                print commands
            # unzip it
            for command in commands:
                os.system(command)
            commands = []
            
            # find slave, adjust target-dir
            dir=self.findSlaveDir(assign(self.systdir),hashing=hashing)
            if dir!=installdir:
                if dir==None:
                    return
                print "Adjusting installdir to '%s'" % dir
                installdir = dir
        if not self.isAmiga:
            print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
            print "Stop."
            return  
        # get slave mit lha
        # echo noline "whdload "
        # lha lq -N %s #?.slave >> t:go
        # create go-file
        if False:
            # old method (use slave name from install archive)
            commands.append('echo ";1" >"%s"' % os.path.join(installdir,"go"))
            # whdload options
            commands.append('echo noline "whdload preload splashdelay=50 quitkey=69 " >>"%s"' % os.path.join(installdir,"go"))
            commands.append('lha lq -N %s #?.slave >>"%s"' % (iname, os.path.join(installdir,"go") ))
            commands.append('echo "fix" >>"%s"' % os.path.join(installdir,"go"))  # to fix display issues that sometimes occur
        else:
            # new method (use slave name that actually made it to installdir)
            commands.append('echo ";1" >"%s"' % os.path.join(installdir,"go"))
            # whdload options
            commands.append('echo noline "whdload preload splashdelay=50 quitkey=69 nocache " >>"%s"' % os.path.join(installdir,"go"))
            slavefile = self.findSlave(assign(self.systdir), hashing=hashing)
            #print slavefile # lha not unpacked on PC
            head, tail = os.path.split(slavefile)
            commands.append('echo "%s" >>"%s"' % (tail, os.path.join(installdir,"go") ))
            commands.append('echo "fix" >>"%s"' % os.path.join(installdir,"go"))  # to fix display issues that sometimes occur

            
            
        # cleanup and show results
        # commands.append('cd %s' %(installdir) ) # don't know how to do renaming of #?.inf to #?.info with AmigaOS, do in Python
        #commands.append('cd "%s"\nlist' % installdir)
        
        # write extra go-file to tempdir if dir has been adjusted (mind the SELF here!)
        if self.isAmiga:
            if installdir != assign(self.tempdir):
                content = ';1\ncd "%s"\nexecute go\n' % installdir
                #print content
                goname=os.path.join(assign(self.systdir),"go")
                h=open(goname, "w")
                h.write(content)
                h.close()

        # recap
        if debug:
            print "\n--> List of commands:"
            for command in commands:
                print command
        
        # go (amiga only)
#        print "\n--> Performing jobs"
        if not self.isAmiga:
           print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
           print "Stop."
           return
           
        # perform action
        for command in commands:
            os.system(command)
            
        # move to managed dir
        if debug:
            print "\nlet's move"
        # 1 - print this dir
        if debug:
            print installdir
        # 2 - print managed dir
        mandir=assign(self.manageddir)
        if debug:
            print mandir
        
        # print entitityname
        basename=data["basename"] # not sure why this was required, but it contained "vision_megademo" otherwise
        if debug:
            print category, basename
        # 3 - copy stuff over
        import shutil
        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir,proddir)
        catdir = os.path.join(mandir,category)
        if not os.path.isdir(catdir):
                # only happens on first occasion of demos/mags/ctros/games
                if verbose:
                    print "Creating '%s'" % (catdir)
                os.makedirs(catdir)
        shutil.copytree(installdir, destdir )
        # 4 only install if basename not in manageddir (done earlier in install)
        # 5 (add remove option)
        
        return

        
    def hashSlavesInLha(self, install, verbose= False):
        '''
        hash all possible slaves (could be install slaves) in install archive and return as list of md5 hashes
        '''
        hashlist = []
        #check and open lha (using http://trac.neotitans.net/wiki/lhafile)
        lhafilename = os.path.join("cache", install)
        if lhafile.is_lhafile(lhafilename):
            f = lhafile.Lhafile(lhafilename)
            # find slave filenames
            flist = []
            for name in f.namelist():
                if name.lower().endswith(".slave"):
                    flist.append(name)
            # hash them all
            if len(flist) >0:
                if verbose:
                    print flist
                for slavename in flist:
                    #s=open((os.path.join(pathname,filename)),"rb").read()
                    m = md5.new()
                    m.update(f.read(slavename))
                    #hashlist.append(m.hexdigest())
                    hashlist.append(base64.urlsafe_b64encode(m.digest()))
                    
                if verbose:
                    print " %s" % hashlist   
            else:
                if verbose:
                    print "- no slave found for %s" % install
        return hashlist
    
    def parseRefsCached(self,debug=False, verbose=False, allow=["demos","ctros","mags","apps","games"], hashing=False):
        s = self.cacheGet(self.url_refs)
        self.parseRefs(s,allow=allow,debug=False, verbose=verbose, hashing=hashing)
        self.saveDict()

    def parseRefs(self, string, debug=False, verbose=False, allow=["demos","ctros","mags","apps"], hashing=False):
        lines = string.splitlines()
        
        iscommentblocks=False       # True while scanning comment lines
        lastlinewascomment=False    # non-commment lines will trigger a new block
        numcommentblocks=0          # counter for simple check
        hadplaceholder=False        # placeholder-block between first and second comment
        placeholderdone=False       # True after placeholder-block has been done, allows for speedup with real data

        # parsing currently only works on pc (some formatting issues)
        if self.isAmiga:
            print "*** Error: reference parsing currently does not work on Amiga\nStop."
            sys.exit()
        
        # get corrections.dict handy
        corrections=eval(open("corrections.dict").read())
        print "loaded corrections.dict" #: %s" %corrections      
        
        for line in lines:
            has_corrections=False # does not mean the file, but will be True is an entity like "Arte" has corrections                      
            if line.startswith("#"):
                # comments
                if lastlinewascomment==False:
                    iscommentblocks=True
                    lastlinewascomment=True
                    # when placeholders are done, we only expect comment and data-lines
                    if hadplaceholder:
                        placeholderdone=True
                if debug:
                    print line
            else:
                if lastlinewascomment:
                    # notice block changes from comment to data
                    numcommentblocks += 1
                    lastlinewascomment=False

                # data-line
                if not placeholderdone:
                    # placeholder/assign block
                    elems = line.split(":=")
                    if debug:
                        print elems, len(elems)
                    if len(elems)!=2:
                        print "*** Warning: unknown line-format: %s" % line
                        break
                    else:
                        # this is a placeholder line with ":=", e.g. "whdload:=http://www.whdload.de/whdload/images/"
                        hadplaceholder=True
                        self.placeholder[elems[0]]=elems[1] # assign placeholder to dictionary
                else:                                             
                    # actual data-lines about games and demos
                    '''
                    expected format, seperated by "#":
                    # database
                    # column contents
                    #   0	category (demos/games/mags/ctros)
                    #   1	basename of install archive, is together with category the primary key
                    #   2	full name of entity, multiple names separated with '*'
                    #   3	vendor
                    #   4	install author, multiple separated with ','
                    #   5	images, multiple separated with ','
                    #   6	hol ids, multiple separated with ',', not for update on hol with prefix '!'
                    #   7	lemon ids, multiple separated with ',', not for update on lemon with prefix '!'
                    #   8	bitworld ids, multiple separated with ','
                    #   9	ada ids, multiple separated with ','
                    #  10	pouet ids, multiple separated with ','
                    '''
                    elems= line.split("#")
                    if len(elems)!=11:
                        print "*** Warning: line has %d instead of 11 elements: %s" %(len(elems),line)
                    else:
                        category = elems[0]
                        basename = elems[1]     # is together with category the primary key
                        name = elems[2]   # multiple names separated with '*'
                        vendor = elems[3]
                        iauthor = elems[4]      # multiple separated with ','
                        images = elems[5]       # multiple separated with ','
                        id_hol = elems[6]
                        id_lemon = elems[7]
                        id_bitworld = elems[8]
                        id_ada = elems[9]
                        id_pouet = elems[10]

                        # apply corrections, step 1
                        if corrections.has_key((category, basename)):
                            has_corrections = True
                        
                        # store entity meta (demos only atm)
                        #if category == "demos":
                        if (category in allow): # and has_image: #after applied corrections
                            install = basename+".lha"
                            info = basename+".html"
                            path_install = category+"/"+install
                            path_info = category+"/"+info
                            url_install=urlparse.urljoin(self.url_whdload,path_install)
                            url_info=urlparse.urljoin(self.url_whdload,path_info)
                            #url=os.path.join(self.url_whdload,category,install)                        
                            
                            s= self.cacheGet(url_install)                                # got cached lha
                            #print "downloading: %s" %url
                                               
                            prodname = name
                            
                            # fill meta data structure
                            meta = {}
                            meta["category"]=category
                            meta["basename"]=basename
                            # construct primary key in a commandline-friendly fashion
                            primary = "%s/%s" % (category, basename)

                            meta["prodname"]=prodname
                            meta["name"]=name
                            meta["vendor"]=vendor
                            meta["iauthor"]=iauthor
                            meta["oimages"]=images
                            meta["id_hol"]=id_hol
                            meta["id_lemon"]=id_lemon
                            meta["id_bitworld"]=id_bitworld
                            meta["id_ada"]=id_ada
                            meta["id_pouet"]=id_pouet
                            
                            meta["fromindex"]="refs.txt"
                            meta["info"]=info
                            meta["install"]=install
                            meta["infoparsed"]=False

                            # apply corrections step 2
                            touchedimages=False
                            if has_corrections:
                                if verbose:
                                    print "  applying corrections for %s (%s), i.e. %s" %(basename, category, corrections[(category,basename)].keys())
                                for key in corrections[(category,basename)].keys():
                                    if key=="images":
                                        touchedimages=True
                                        #if debug:
                                        #    print "touched %s of %s" % (key,name)
                                        #sys.exit()
                                    # this worked great up to v0.11, but caused a lot of boiler plate when dealing e.g. with "copyas"
                                    meta[key]=corrections[(category,basename)][key]
                                    
                                    # therefore try a more clever approach with dict copy, one day ;)
                                    #meta[key]=corrections[(category,basename)][key]
                                    
                                meta["fromindex"]="corrections.dict"
                            
                            if not touchedimages:
                                #print images
                                images = self.buildImagesMeta(prodname, images,debug=self.debug,verbose=self.verbose, primary=primary)
                                # set images and consider special case for "ctros"
                                if category!="ctros":
                                    meta["images"]=images
                                else:
                                    meta["images"]=None
                            touchedimages=False
                            
                            # hash slaves if hashing enables
                            hashlist= []
                            if hashing:
                                # check and open lha (using http://trac.neotitans.net/wiki/lhafile)
                                hashlist = self.hashSlavesInLha(install)
                                #lhafilename = os.path.join("cache", install)
                                #if lhafile.is_lhafile(lhafilename):
                                #    f = lhafile.Lhafile(lhafilename)
                                #    # find slave filenames
                                #    flist = []
                                #    for name in f.namelist():
                                #        if name.lower().endswith(".slave"):
                                #            flist.append(name)
                                #    # hash them all
                                #    if len(flist) >0:
                                #        if verbose:
                                #            print flist
                                #        for slavename in flist:
                                #            #s=open((os.path.join(pathname,filename)),"rb").read()
                                #            m = md5.new()
                                #            m.update(f.read(slavename))
                                #            hashlist.append(m.hexdigest())
                                #        if verbose:
                                #            print " %s" % hashlist   
                                #    else:
                                #        if verbose:
                                #            print "- no slave found for %s" % install
                                      
                                # get old installs linked in html under "old install" section as well
                                listOfOldInstallArchives = self.getOldInstalls(install, url_info) # got cached html info
                                # get tail of each href
                                oldinstalls = []
                                for href in listOfOldInstallArchives:
                                    head, oldinstall = os.path.split(href)
                                    print "    hashing: %s" %oldinstall
                                    oldinstalls.append(oldinstall)
                                    hashlist.extend(self.hashSlavesInLha(oldinstall))
                                
                                #print listOfOldInstallArchives

                            # save to seperate dict
                            meta["md5"]=hashlist
                            
                            #if name=="Arte":
                            #    print meta
                            if has_corrections and debug:
                                print meta
                                print
                                
                            # store this entry and prepare for next loop
                            self.brain["prods"][primary] = meta
                            # count some stats (todo: avoid double counting -> seperate function)
                            self.dh.countToDict(self.brain["stats"]["category"], category)
                            self.dh.countToDict(self.brain["stats"]["vendor"], vendor)
                            self.dh.countToDict(self.brain["stats"]["iauthor"], iauthor)
                            has_corrections=False   # reset for next loop

                            # save precious debugging time by reducing turn around with lots of http connections
                            if debug:
                                self.saveDict()
                                
                            #else:
                            #    #if debug:
                            #    print "*** Warning: cleaning due to missing images: %s (%s)" % (prodname,meta["images"])
                            #if debug:
                            #    if prodname == "Roots":
                            #        print meta
                                    
                        else:
                            if debug:
                                #print "*** Skipping: %s" % name
                                pass
                                        
            
        if debug:
            print "\n\nnumcommentblocks: %d" % numcommentblocks
            #print "\nplaceholders= %s" % self.placeholder
            print "\ncategories: %s" % self.brain["stats"]["category"]
            #print "\nvendors: %s" % self.stat_vendor # could be used to list by group/vendor
            #print "\nimage authors: %s" % self.stat_iauthor

    def getOldInstalls(self, install, url_info, debug=False):
        '''
        investigate supplied url for linked "old install" lha archives of the install.
        get a local copy of each of them and return list of names (ready to be stored as "installs_old")
        '''
        #if debug:
        print install, url_info
        s = self.cacheGet(url_info)
        #print url_info
        #if url_info =="http://www.whdload.de/games/1943.html":
        hrefs=[]
        if s.find("Old Install Archives")!=-1:
            w = BeautifulSoup(s)
            # get list of all hrefs referring to ".lha"
            #lhas = w.find_all(href=re.compile(".lha"))
            th=w.find("th", text=re.compile("Old Install"))
            if th!=None:
                if debug:
                    print th
                tr=th.parent
                if tr!=None:
                    if debug:
                        print tr
                    table=tr.parent
                    if debug:
                        print table

                    if table!=None:
                        lhas = table.find_all("a", href=re.compile(".lha"))
                        if debug:
                            print "found %d entries" % (len(lhas))
                            print lhas
                            print
                            print url_info
                        
                        # iterate over list and store old hrefs
                        for a in lhas:
                            href = a["href"]
                            #print href
                            if debug:
                                print href
                            if href != install:
                                fullhref = urllib.basejoin(url_info,href)
                                hrefs.append(fullhref)
                       
                        if debug:
                            print
                            print hrefs
                        
                        # get a local copy of all of them
                        for href in hrefs:
                            print "  downloading old install: '%s'" % href
                            self.cacheGet(href)
                    
                    #print install
        else:
            pass
            #print "*** Info: no old installs"
            #sys.exit()
        return hrefs
    
    def cleanRefsCached(self, debug=True,verbose=False,hashing=False):
        '''
        removes all entities without images, recalc stas and saves the brain-file
        '''
        # step over all prods
        #print "---> Cleaning"
        #self.getStats()
        newdict={}
        newdict["prods"]={}
        newdict["stats"]={}
        
        #dicts for stats, filled by parseRefs, reachable from getStats()
        newdict["stats"]["category"]={}
        newdict["stats"]["vendor"]={}
        newdict["stats"]["iauthor"]={}
                
        for name in self.brain["prods"]:
            #print self.brain["prods"][name]
            #print name
            #if len( str(self.brain["prods"][name]["images"]) )>2 or name=="games/Unreal" or (hashing and len(self.brain["prods"][name]["md5"])>0):
            if len( str(self.brain["prods"][name]["images"]) )>2 or (hashing and len(self.brain["prods"][name]["md5"])>0):
                # quick check okay, i.e. more than "{}"
                # copy over entry
                #print "keep %s" % name
                newdict["prods"][name]=self.brain["prods"][name]
                #print self.brain["prods"][name]["category"]
                self.dh.countToDict(newdict["stats"]["category"], self.brain["prods"][name]["category"])
                self.dh.countToDict(newdict["stats"]["vendor"], self.brain["prods"][name]["vendor"])
                self.dh.countToDict(newdict["stats"]["iauthor"], self.brain["prods"][name]["iauthor"])
            else:
                # remove this prod from brain, i.e. do not copy
                #print "remove %s" %name
                #sys.exit()
                self.dh.logValueToDict(self.errors,"cleaned",name)
                if verbose:
                    print "remove %s (%s)" % (name,self.brain["prods"][name]["images"])
                pass
        
        # set newdict as brain
        #self.brain = newdict # too much, be more subtle
        numwas = len(self.brain["prods"]) 
        numis = len(newdict["prods"])
        diff = numwas-numis
        
        print "Cleaning removed %s productions without images from brain-file (from %s to %s)" % ( diff, numwas, numis )
        if diff!=0:
            print "  old brain contained %s vendors in %s categories %s" % (len(self.brain["stats"]["vendor"]), len(self.brain["stats"]["category"]), self.brain["stats"]["category"])
            print "  new brain contains %s vendors in %s categories %s" % (len(newdict["stats"]["vendor"]), len(newdict["stats"]["category"]), newdict["stats"]["category"])
        else:
            print "  brain contains %s vendors in %s categories %s" % (len(newdict["stats"]["vendor"]), len(newdict["stats"]["category"]), newdict["stats"]["category"])

        self.brain["prods"]=newdict["prods"]
        self.brain["stats"]=newdict["stats"]
        
        #self.getStats()
        self.saveDict()
        

def test(demo,debug=False,verbose=True,hashing=False):
    #has = demos.hasDemo(demo)
    #print "has: %s" % has
    print
    if debug:
        print "%s, %s" % (demo, has)
    #if has:
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)
    # try to install
    demos.install(demo, debug=debug, verbose=verbose,hashing=hashing)

def installWild(demo,debug=False,verbose=True,hashing=False,force=False):
    # implemented wildcard matching for installs as in http://docs.python.org/2/library/fnmatch.html
    print
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)

    if demo.find("*")==-1:
        # no wildcard
        demos.install(demo, debug=debug, verbose=verbose,hashing=hashing)
    else:
        # with wildcard
        import fnmatch
        entities=demos.brain["prods"].keys()
        matched=[]
        for entity in entities:
            if fnmatch.fnmatch(entity, demo):
                #print entity
                # try to install
                matched.append(entity)
        # 
        entities = len(matched)
        print "Matched %s entities with '%s'" %(entities,demo)
        if force:
            count=1
            for entity in matched:
                sys.stdout.write("---> %s of %s (%.1f %%): " % (count, entities, float(count/float(entities)*100.0)))
                count = count+1
                demos.install(entity, debug=False, verbose=False, hashing=hashing)
        else:
            for entity in matched:
                print " %s" %entity
            print "\nSupply -f option if you want to install all this (%s entities)." % entities
        
def removeWild(demo,debug=False,verbose=True,hashing=False,force=False):
    # attempt to implement wildcard matching for installs as in http://docs.python.org/2/library/fnmatch.html
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)

    if demo.find("*")==-1:
        # no wildcard
        demos.removeinstall(demo, debug=debug, verbose=verbose,hashing=hashing)
    else:
        # with wildcard
        import fnmatch
        entities=demos.brain["prods"].keys()
        matched=[]
        for entity in entities:
            if fnmatch.fnmatch(entity, demo):
                #print entity
                ismanaged=demos.isManaged(entity)
                # check if dir exists
                if ismanaged:
                    matched.append(entity)
        # 
        entities = len(matched)
        print "Matched %s entities with '%s'" %(entities,demo)
        if force:
            count=1
            for entity in matched:
                sys.stdout.write("---> removing %s of %s (%.1f %%): %s .. " % (count, entities, float(count/float(entities)*100.0), entity))
                count = count+1
                demos.removeinstall(entity, debug=False, verbose=False, hashing=hashing)
        else:
            for entity in matched:
                print " %s" %entity
            print "\nSupply -f option if you want to remove all this (%s entities)." % entities


def test2():
    self.parseRefsCached()
    self.saveDict()

#---get the arguments
print "Wim.py v0.3, WHDLoad Install Manager by Noname (20.11.2013)"

optlist, args = getopt.getopt(sys.argv[1:],'i:vl:bcr:se:hf')
if len(optlist)==0:
    print "  automates your WHDLoad installation chores"
    print 
    print "Options:"
    print "  -b  build index"
    print "  -c  clean index"
    print "  -s  stats"
    print "  -e  investigate exceptions"
    print "  -v  be verbose (lots of output)"
    print "  -h  hashing"
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
    print "  wim.py -i megademo (try this and feel the ambiguity of the word)"
    print "  wim.py -i digitech_megademo (install Digitech Megademo)"
    print "  wim.py -i *megademo* (check everything with Megademo in it)"
    print "  wim.py -fi *megademo* (actually install everything with Megademo in it)"
    print "  wim.py -fr *megademo* (and remove everything with Megademo in it)"
    print
    print "  wim.py -l ctros (list cracktros)"
    print "  wim.py -i swiv (install SWIV cracktro by Skid Row)"
    print "  wim.py -l games (list games)"
    print "  wim.py -i Katakis (install the game Katakis - matching on name)"
    print "  wim.py -i games/Katakis (same, but matching on primary key)"
    print
    print "Note:"
    print "  wim.py currently only installs to a tempdir in 't:'"
    print "  It cleans that place prior to any install, so no need to do it by hand."
    print "  You don't have to manually cd there and find the right file to start."
    print "  Instead just issue the 'j' command, which auto-starts the last install!"
    #sys.exit()
 
#print optlist, args       

# instantiate
demos = whdloadProxy()

for o, a in optlist:
    print o, a



    if o== "-h":
        print " hashing enabled"
        have_h=True

    if o== "-c":
        #print "  cleanRefs()"
        have_c=True
        #demos.cleanRefsCached()

    if o== "-e":
        #print "  error()"
        have_e_a=a
        have_e=True

    if o== "-l":
        #print "  list known %s" % a
        have_l = True
        #demos.getKnownEntities(a)
        #sys.exit()

    if o== "-s":
        have_s=True
        #print "  list stats" % a
        #demos.getStats()
        #sys.exit()

    if o == "-v":
        print "  be verbose"
        g_debug=True
        g_verbose=True
        demos.setVariables(debug=g_debug, verbose=g_verbose)

    if o == "-b":
        #print "  build tables"
        have_b = True
        
        #demos.buildTables(recursive=True)
        #sys.exit()

    if o == "-f":
        have_f=True

    if o == "-i":
        have_i=True
        installname=a
        
    if o== "-r":
        have_r=True
        removename=a
        
    #    if o == "-c":
    #print "  capabilities are: 'urllib'-%s, 'bs4'-%s" % (q(config["has_urllib"],"True","False"), q(config["has_bs4"],"True","False"))


# execute actions
errorsloaded=False
if have_b:
    print "\n---> Building Index"
    demos.parseRefsCached(verbose=g_verbose, hashing=have_h)
    #demos.buildTables(recursive=True)
    errorsloaded=True


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
    #print "\n---> Installing"
    installWild(installname,debug=False,verbose=False,hashing=have_h, force=have_f)

if have_r:
    removeWild(removename,debug=False,verbose=False,hashing=have_h, force=have_f)


#print demos.brain

# noch nicht unterstuetzt:
# Audio Violation - guter Test for rawdic Datei extrahierung
# Arte - 1 Disk 2 Files, not linked in index
# Chromagic - dms link aus text beschreibung pulen
# Dance Diverse Vol.1, Delirium, most Megademos - error 205
# Digital Complexity - nicht Disk.1 sondern data (und dann fehler)
# Project Techno - Archive Fehler? go kaputt
# The Simpsons - .lha lag nicht im cahcedir




#test("Dizzy Tunes")
#test("Dizzy Tunes 2")
#test("Face Another Day")
#test("Voyage")

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






