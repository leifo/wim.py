#!/usr/bin/env python
import urlparse

import lhafile

import wicked.cache
import wicked.helpers
from wicked.assigns import *
from wicked.io.copyjob import copy
from wicked.io.dmsjob import undms
from wicked.io.joblist import joblist
from wicked.io.lhajob import unlha
from wicked.io.renamejob import rename
from wicked.io.zipjob import unzip
from wicked.rapath import raPath

try:
    from bs4 import BeautifulSoup
except:
    pass

# only needed for build-hashing (-bh)
import re, urllib


class whdloadproxy:
    config = {}

    # url_all= "http://www.whdload.de/demos/all.html"
    # url_allv = "http://www.whdload.de/demos/allv.html"
    # url_path = "http://www.whdload.de/demos/" # deprecated since 0.04

    url_whdload = "http://www.whdload.de/"
    url_refs = "http://whdload.de/db/refs.txt"
    placeholder = {}

    lastt = None

    # prods = {}  # results will go here
    brain = {}  # results will go here
    dh = None

    debug = False
    verbose = False
    errors = {}
    hashes={} # !!!

    # needed to finding the slave in a subdir after unpacking slave lha
    slavesfound = []

    def __init__(self, config={}):
        self.config = config  # put a wim.py config here

        # !!! init stuff moved here to maintain self
        self.manageddir = config["manageddir"]
        self.arcdir = config["arcdir"]
        self.cachedir = config["cachedir"]
        self.tempdir = config["tempdir"]
        print "\n  Tempdir located at: %s" % self.tempdir
        self.ramtempdir = config["ramtempdir"]    # amiga has its temp-device in ram, that's faster & avoids disk-usage
        # we work in our own subdir in ramtempdir
        self.scratchdir = os.path.join(self.ramtempdir, config["scratchdirsuffix"])

        self.isAmiga = -1

        t1 = time.clock()
        self.dh = wicked.helpers.dicthelpers()
        self.lh = wicked.helpers.listhelpers()
        if self.checkConfig():
            # cant currently build on Amiga Python 2.0
            # self.buildTables(recursive=False)
            # self.saveDict()
            self.loadDict()
            pass
        else:
            self.loadDict()
        self.loadHashes()
        t2 = time.clock()
        print "done in %.2f seconds." % (t2 - t1)

        # create t: replacement if not on Amiga
        if not os.path.isdir(assign(self.ramtempdir)):
            self.ramtempdir = self.tempdir
            print "Not running on Amiga, assign t: to /tempdir" # todo: double-check this path

        # setup cache-dirs
        self.cache = wicked.cache.cache(self.cachedir)
        self.tempcache = wicked.cache.cache(self.tempdir)

    def setVariables(self, debug=False, verbose=False):
        '''
        external interface for internal state variables
        '''
        self.debug = debug
        self.verbose = verbose

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

        # print "Running Python v%d.%d.%d on %s - %s" % (major,minor,micro,platform,sys.version)
        # print "  capabilities are: 'urllib'-%s, 'bs4'-%s, 'amiga'-%s" % (q(config["has_urllib"],"True","False"), q(config["has_bs4"],"True","False"), q(config["is_amiga"],"True","False"))
        pstring = wicked.helpers.getPlatformString()
        print "  running on Python v%d.%d.%d on %s" % (major, minor, micro, pstring)

        # check bs4 requirements
        # http://www.crummy.com/software/BeautifulSoup/ -> Beautiful Soup 4 works on both Python 2 (2.6+) and Python 3.
        okversion = False
        if major >= 2:
            if major == 2 and minor >= 6:
                # 2.6+
                okversion = True
            elif major == 3:
                okversion = True

        # check bs4 availability 
        if okversion:
            # todo, maybe
            pass

        print
        if okversion:
            # print "--> generator functionality (scrape website, build tables)"
            self.isAmiga = False
        else:
            # print "--> installer functionality (install)"
            self.isAmiga = True

        #print "self.isAmiga = %s" % self.isAmiga
        sys.stdout.write("Initializing ... ")

        return okversion

    def saveDict(self):
        self.dh.saveDictionary(repr(self.brain), "data/brain.dict")
        # print "***PICKLING"
        #filehandle = open("data/brain.pickle", "wb")
        #pickle.dump(self.brain, filehandle)
        #filehandle.close()

        # save good content to seperate file to save time upon rebuilding
        if not self.brain.has_key("content"):
            self.brain["content"] = {}
        self.dh.saveDictionary(repr(self.brain["content"]), "data/brain-content.dict")

        # save errors to seperate file to facilitate reading amd save time when not needed, i.e. on Amiga when not using -s or -e
        self.dh.saveDictionary(repr(self.errors), "data/errors.dict")

        return

        # !!!

    def loadHashes(self):
        if self.hashes=={}:
            #try:
            #    filehandle = open("brain-hashes.pickle","r")
            #    self.hashes = pickle.load(filehandle)
            #    filehandle.close()
            #except:
            #    self.hashes=self.dh.loadDictionary("brain-hashes.dict")
            #self.dh.saveDictionary(self.hashes,"brain-hashes.dict")
            self.hashes = self.dh.loadDictionary("data/brain-hashes.dict")
        print " know %s hashes\n" % len(self.hashes)

    def loadDict(self):
        try:
            self.brain = eval(self.dh.loadDictionary("data/brain.dict"))
            #filehandle = open("data/brain.pickle", "r")
            #self.brain = pickle.load(filehandle)
            #filehandle.close()
        except:
            self.brain = {}
            self.brain["prods"] = {}
            self.brain["stats"] = {}
            # dicts for stats, filled by parseRefs, reachable from getStats()
            self.brain["stats"]["category"] = {}
            self.brain["stats"]["vendor"] = {}
            self.brain["stats"]["iauthor"] = {}
            # needed by buildImagesMeta to keep track of links that have no content-length (i.e. dirs)
            self.brain["nocontent"] = {}
            self.brain["content"] = {}
        try:
            self.brain["content"] = eval(dh.loadDictionary("data/brain-content.dict"))
        except:
            # print "*** Error: Can't load 'prods.dict'. Run this on Windows first!"
            pass

        # make sure to have dicts in place        
        if not self.brain.has_key("content"):
            self.brain["content"] = {}
        if not self.brain.has_key("nocontent"):
            self.brain["nocontent"] = {}
        if not self.brain.has_key("noconnection"):
            self.brain["noconnection"] = {}

    def loadErrors(self):
        '''
        load errors from file, in case user wants to investigate them, e.g. -s or -e option
        '''
        self.errors = eval(self.dh.loadDictionary("data/errors.dict"))

    def expandPlaceholders(self, url, debug=False):
        '''
        uses self.placeholder to expand url to original state
        '''
        if url == "http://ftp.amigascne.org/pub/amiga/Groups/B/Bastards":
            pass

        # print url
        if url.startswith("http"):
            # no expansion needed
            return url
        if url.startswith("ftp"):
            # no expansion needed
            return url

        elem = url.split(":")
        if len(elem) != 2:
            # don't know
            if debug:
                print "*** Warning: placeholder error with: %s (%s)" % (url, str(elem))
            return url

        '''
        url="aminet:demo/aga/sanity_roots.dms"
        {'aminet': 'http://www.aminet.net/'}
        
        '''
        # substitute placeholder
        if self.placeholder.has_key(elem[0]):
            # print elem[0], elem[1]
            return self.placeholder[elem[0]] + elem[1]
        # otherwise just return input
        return url

    def investigateLinkForContent(self, url, debug=True, verbose=False):
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
        # if url=="ftp://ftp.amigascne.org/pub/amiga/Groups/U/United_Forces/UFO-Sensenmann":
        # if url=="http://ftp.amigascne.org/pub/amiga/Groups/B/Bastards":
        #    print "*** Info: hard coded breakpoint"
        #    #return True

        # step 1 - check if we had been here before and take shortcut if we have
        # there are many repetitive links in whdload data, e.g. ftp://ftp.funet.fi/pub/amiga/demos/Silents (dir rather than actual file) 

        if self.brain["nocontent"].has_key(url):
            if verbose:
                print "%s - * NO CONTENT (cached) *" % url
            return False, True  # no content, connection ok (cached)

        if self.brain["noconnection"].has_key(url):
            if verbose:
                print "%s - * NO CONNECTION (cached) *" % url
            return False, False  # no content, connection ok (cached)

        if verbose:
            sys.stdout.write("\n*** Info: Investigating '%s' .. " % (url))

        # step 2 - check for 302 redirects TODO: fix and handle 302 correctly
        print "url: %s\n" % url
        try:
            h=urllib.urlopen(url)
            redirect = False;
            if h.geturl() != url:
                print "caught a redirect for %s\n\n" % url
                redirect = True
        except:
            return False,False

        # step 3 - open the url for inspection, get headers into d
        try:
            h = urllib.urlopen(url)
            d = h.headers.dict
            if d.has_key("content-length"):
                cl = d["content-length"]
                ct = ""
                if d.has_key("content-type"):
                    ct = d["content-type"]
                if verbose:
                    sys.stdout.write("length: '%s', \ntype: '%s'\n" % (cl, ct))
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
            return False, False  # no content, connection FAILED

        # step 4 - passed all tests, should be okay so far, done
        print "***Info: Accepted as 'content': %s\n" % url
        self.dh.countToDict(self.brain["content"], url)
        # also double-log to errors, to make it browsable via the -e option
        # self.dh.countToDict(self.brain["content"], url)
        self.dh.logValueToDict(self.errors, "content", url)
        return True, True  # content ok, connection ok! (we want more of this :)

    def buildImagesMeta(self, prodname, hint, debug=False, verbose=False, allow=[".dms", ".adf", "", ".exe", ".lha"],
                        primary=None):
        '''
        consume non deterministic pointer to images and try to be clever about it
        input: last entry from the line from the list of installs
        out dictionary with 
        '''
        # quick out if images is already a dict not a str
        if type(hint) == "dict":
            return hint  # means that it was most probably already fixed or corrected

        # if primary is given use that for logging errors
        if primary != None:
            errorname = primary
        else:
            errorname = prodname

        # expand hint using placeholder
        # e.g. amigascne: -> http://ftp.amigascne.org/pub/amiga/Groups/
        hintfull = self.expandPlaceholders(hint)

        # if demo=="Roots":
        # if hint=="ftp://ftp.amigascne.org/pub/amiga/Groups/U/United_Forces/UFO-Sensenmann": # done - added allowed extension ""
        # if hintfull=="http://ftp.amigascne.org/pub/amiga/Groups/C/Channel_42":

        # if hintfull=="http://ftp.amigascne.org/pub/amiga/Groups/B/Bastards":
        #    print "*** Info: caught specimen"

        # define for safety
        content = False
        connection = False
        lateaccept = False  # will be true if investigatelink confirmed content in hintfull, e.g. animotion

        if True:
            # print "--> parsing image locations"
            # one disks first, start with dms

            # get basename

            # todo: geturl fuer php endungen

            seenat, filename = os.path.split(hintfull)
            # seenat = self.expandPlaceholders(seenat) # done above
            if len(filename) == 0:
                # at this point it is unclear if we have a file (no known extension, could also be a directory)
                # (e.g. ftp://ftp.amigascne.org/pub/amiga/Groups/P/Phenomena/PHENOMENA-Animotion)
                # therefore investigate the link in seenat
                if len(seenat) > 0:
                    if debug:
                        sys.stdout.write("\n%s, " % (prodname))
                    content, connection = self.investigateLinkForContent(seenat, debug=debug, verbose=verbose)
                    if not content and connection:
                        self.dh.logValueToDict(self.errors, "nocontent", errorname)
                        return {}
                    elif not connection:
                        if verbose:
                            print "*** Warning: connection error - skipping"
                            # print self.brain["noconnection"][seenat]   # print counter of occurences

                else:
                    # empty hint
                    self.dh.logValueToDict(self.errors, "emptyhint", errorname)
                    if verbose:
                        print "*** Warning: no direct link to: %s (%s)" % (prodname, hint)
                    return {}

            # get suffix
            trash, ext = os.path.splitext(hintfull)
            ext = ext.lower()

            if len(ext) == 0:
                # at this point it is unclear if we have a file (no known extension, could also be a directory)
                # (e.g. ftp://ftp.amigascne.org/pub/amiga/Groups/P/Phenomena/PHENOMENA-Animotion)
                # therefore investigate the link in hint/hintfull
                if len(hintfull) > 0:
                    if debug:
                        sys.stdout.write("\n%s, " % (prodname))
                    # hinturl=self.expandPlaceholders(hint) # done above
                    if not self.brain["content"].has_key(hintfull):
                        content, connection = self.investigateLinkForContent(hintfull, debug=debug, verbose=verbose)
                        if not content and connection:
                            self.dh.logValueToDict(self.errors, "nocontent", errorname)
                            return {}
                        elif not connection:
                            if verbose:
                                print "*** Warning: connection error - skipping"
                                # print self.brain["noconnection"][hintfull]    # print counter of occurences
                        # last check: hint must not end on "/" otherwise it cannot be a file
                        if not hintfull.endswith("/"):
                            lateaccept = True  # now this should be usable content that just had no extension
                else:
                    # empty hint
                    self.dh.logValueToDict(self.errors, "empty hint", errorname)
                    if verbose:
                        print "*** Warning: no direct link to: %s (%s)" % (prodname, hinturl)
                    return {}

                # my hinge is that this would be demos from the content dict like animotion
                if ext == "" and lateaccept:
                    pass  # print "breakpoint"

            # check for allowed extensions
            if ext not in allow:
                self.dh.logValueToDict(self.errors, "%s" % ext, errorname)
                if verbose:
                    print "*** Warning: unsupported extension '%s' for '%s' ('%s','%s')" % (ext, prodname, hint, seenat)
                return {}
            if debug:
                print prodname, seenat, filename, ext

            # print "still here"

            # pack it up
            diskimages = {}
            disk = []  # list because there could be several images per disk (dms frequently 2 per disk)
            image = {}
            image["file"] = filename
            image["seenat"] = seenat
            image["type"] = ext  # reconsider after adding the other types

            disk.append(image)
            diskimages[1] = disk

            return diskimages
        else:
            return {}

    def parseInfo(self, demoname, debug=True):
        '''
        Parses info page of prod demoname upon request
        '''
        if self.config["has_bs4"] == False:
            return
        # s = self.cacheGet(self.url_path + self.brain["prods"][demoname]["infox"])
        #!!!todo:fixme new cache url for infopage in parseInfo
        url = os.path.join(self.url_whdload,  self.brain["prods"][demoname]["category"], self.brain["prods"][demoname]["info"])
        s = self.cache.get(url)
        ###    self.url_whdload + self.brain["prods"][demoname]["category"] + self.brain["prods"][demoname]["info"])
        # parse html

        if debug:
            string = "Parsing info for '%s' .. " % (demoname)
            sys.stdout.write(string)
        else:
            # sys.stdout.write(".")
            pass

        w = BeautifulSoup(s,"html.parser")

        if debug:
            print w

            print "*** End info"

        # collect table rows
        # tr= w.find_all("tr")
        # print "found %d entries" % (len(tr))

        # mark as done
        self.brain["prods"][demoname]["infoparsed"] = True
        return

    def hasDemo(self, demoname):
        '''
        Return True if demoname is known
        '''
        return self.brain["prods"].has_key(demoname)

    def getMeta(self, demoname, debug=False):
        if self.hasDemo(demoname):
            if self.brain["prods"][demoname]["infoparsed"] == False:
                # get details
                self.parseInfo(demoname, debug)
            return self.brain["prods"][demoname]
        else:
            return None

    def getBrain(self):
        '''
        quick hack of not printing (so not using the other hack) for testing the bottle.py web ui
        '''
        return self.brain

    def getKnownEntities(self, category):
        '''
        prints all currently known and supported entitites of a certain category. prints all if category is ""
        '''
        if category == "":
            p = True
        else:
            p = False
        for prod in self.brain["prods"].keys():
            if p or self.brain["prods"][prod]["category"] == category:
                entity = self.brain["prods"][prod]
                # print entity
                images = entity["images"]
                if images != None:
                    numdisks = len(images)
                else:
                    numdisks = "No"
                print "%s by %s (%s - %s disks)" % (entity["prodname"], entity["vendor"], entity["basename"], numdisks)
                # print "%s by %s (type s)" % (entity["prodname"], entity["vendor"])
        if category not in self.brain["stats"]["category"].keys():
            sys.stdout.write("Supplied argument '%s' is no known category." % category)
            print " Consider using one of: %s" % self.brain["stats"]["category"].keys()

    def getError(self, error):
        '''
        more details on occurences of error/exceptions
        '''
        if self.errors.has_key(error):
            elems = self.errors[error]
            print "Exploring '%s' which occured %d times:" % (error, len(elems))
            for elem in elems:
                if self.brain["prods"].has_key(elem):
                    print "  %s, %s" % (elem, self.brain["prods"][elem]["oimages"])
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
        # 1. compute "uncertainty" list, where links are given but no image has been recognized
        # no direct link, missing images
        # l1=self.errors["no direct link"]
        # l2=self.errors["missing images"]
        # uncertain = self.lh.difference(l1,l2)
        # uncertain = filter(lambda x:x not in l2,l1)
        # uncertain = list(set(l1) and set(l2))
        # uncertain = list(set(l1) - set(ncertain))
        # uncertain = self.lh.difference(self.errors["no direct link"], self.errors["missing images"])
        uncertain = None
        if uncertain != None:
            for elem in uncertain:
                self.dh.logValueToDict(self.errors, "uncertain", elem)

        # print "Common errors: %s" % str(self.errors.keys())
        print "Known categories: %s" % str(self.brain["stats"]["category"])

        # stats on install methods
        method = {0:0,1:0,2:0,3:0,4:0,5:0,-1:0, 6:0}
        for prod in self.brain["prods"]:
            #print self.brain["prods"][prod].keys()
            #['category', 'info', 'prodname', 'vendor', 'name', 'oimages', 'basename', 'installmethod',
            # 'fromindex', 'id_hol', 'id_bitworld', 'id_ada', 'install', 'id_lemon', 'images', 'iauthor', 'infoparsed', 'md5', 'id_pouet']
            #self.dh.logValueToDict(method,self.brain["prods"][prod]["installmethod"], self.brain["prods"][prod]["basename"])
            self.dh.countToDict(method,self.brain["prods"][prod]["installmethod"])
        #print "Install methods: %s " % method
        print "Install methods: Unknown (-1): %d, RawDIC (0): %d, Patcher (1): %d, DIC (2): %d\n  Files (3): %d, CD (4): %d, SingleFile (5): %d, Arcadia (6): %d" % \
              (method[-1], method[0],method[1],method[2],method[3],method[4],method[5], method[6])
        #{0=RawDIC: 128, 2: 181, 3: 132, 4: 2, 5: 61, None: 156}
        #(0=RawDIC: %d,  1=Patcher: %d, 2=DIC: %d, 3=Files: %d, 4=CD: %d 5=SingleFile, %d)

        # 2. sort and display results (currently not python v2.0 compatible, i.e. not on Amiga)
        # sorted([('abc', 121),('abc', 231),('abc', 148), ('abc',221)],key=lambda x: x[1])

        print "\nExceptions while parsing references:"
        tuplelist = []
        for error in self.errors.keys():
            count = len(self.errors[error])
            tuplelist.append((error, count))

        # sorted fails on Python 2.0, so just try
        try:
            # pc
            sortedtuplelist = sorted(tuplelist, key=lambda x: x[1])
            for tuple in sortedtuplelist:
                print "  %s : %s" % (tuple[0], tuple[1])
        except:
            # amiga
            for tuple in tuplelist:
                print "  %s : %s" % (tuple[0], tuple[1])

        print '\nTip: use -e option to explore occurences, e.g. -e "nocontent"'

    def buildTables(self, recursive=False, debug=False):
        '''
        Cache relevant content and parse demo list
        '''
        # self.parseIndexAll(recursive=recursive, debug=False)
        # self.parseIndexAllV(recursive=recursive, debug=False)
        self.parseRefsCached()

    def collection_helper(self, arg, dirname, names, debug=False):
        '''
        os.path.walk helper for findSlaves. look there for more details.
        '''
        counter = 0
        if debug:
            print "  dir '%s' has %s files" % (dirname, len(names))
        if dirname.endswith("cache"):
            print "skipping cache"
            return
        for name in names:
            # fullname = dirname+name

            propername = os.path.join(dirname, name)
            fullname = propername

            # print "dir: '%s', name: '%s', fullname: '%s'" % (dirname,name,fullname)
            # print "dir: '%s', name: '%s', fullname: -" % (dirname,name)

            if name.lower().endswith(arg.lower()):
                # fullname = os.path.normpath( dirname + name )
                # fullname = os.path.join(dirname, name)
                # print name
                # print fullname
                # print "isFile: " + fullname + "("+dirname+"  "+name+")"
                self.slavesfound.append(propername)
                # if os.path.isdir(fullname):
                #    #print "isDir: " + fullname + "("+dirname+"  "+name+")"
                #    names.remove(name)

    def haveHash(self, md5hash):
        '''
        return True/False if md5hash is known
        '''
        res = False
        res=self.hashes.has_key(md5hash)
        #hashdir = os.path.join("data", "hashes")
        #filename = os.path.join(hashdir, md5hash)
        ## print filename
        #res = os.path.isfile(filename)
        # print res
        return res

    def getHash(self, md5hash):
        '''
        return value for key md5hash or None
        '''
        # print "**********"
        if not self.haveHash(md5hash):
            return None
        return self.hashes[md5hash]

        #hashdir = os.path.join("data", "hashes")
        #filename = os.path.join(hashdir, md5hash)
        ## print filename
        #s = open(filename).read()
        ## print s
        #return eval(s)

    def findHashRoute(self, md5hash, debug=False):
        '''
        try to work out unpack route based on md5hash of this install
        !only works with hashing enabled!
        return list of steps
        '''
        # if not self.hashes.has_key(md5hash):
        if not self.haveHash(md5hash):
            return []

        # step through list of known sightings and find route to top-file
        # listhashes = self.hashes[md5hash] #!!!
        # print "***LEIF"
        listhashes = self.getHash(md5hash)
        # print listhashes
        route = []
        sight = listhashes[0]
        if debug:
            print listhashes
        while sight["type"] != "f":
            # print sight
            route.append(sight)
            # sightlist=self.hashes[sight["in"]] # !!!
            sightlist = self.getHash(sight["in"])
            # print sightlist
            sight = sightlist[0]
        # print sight
        route.append(sight)
        # print "*** Info: route"
        # print route
        return route

    def findSlaves(self, dirname, debug=False, hashing=False, verbose=False):
        '''
        Input> base dirname for recursive search
        Output> list of matching slave-filenames
        '''
        self.slavesfound = []  # cleanup

        # get full absolute path from relative os.curdir
        (path, success) = raPath(dirname)  # needed
        if not success:
            print "***Error: Problem getting absolute path for dirname '%s'.\nStop." % dirname
            print dirname, path, success
            sys.exit()

        searchfor = ".slave"
        if debug:
            print "curdir: '%s', pardir: '%s', sep: '%s'" % (curdir, pardir, sep)
        if verbose:
            print "findSlave: looking for '%s' files in '%s'" % (searchfor, path)

        # append matching filenames to self.slavesfound
        os.path.walk(dirname, self.collection_helper, searchfor)

        # hacked hashing in here, could be seperated later
        for file in self.slavesfound:
            if hashing:
                if debug:
                    print "%s is file: %s" % (file, os.path.isfile(file))
                # lets hash it
                s = open(file, "rb").read()
                m = md5.new()
                m.update(s)

                # md5hash = m.hexdigest()
                # md5hash= base64.urlsafe_b64encode(m.digest())
                # make urlsafe on amiga without b64encode according to http://pymotw.com/2/base64/
                digest=m.digest()
                #t1 = base64.encodestring(digest)
                #t2 = t1.replace("/", "_")
                #md5hash = t2.replace("+", "-") # has trailing \n, why did this work before?
                md5hash = base64.urlsafe_b64encode(digest)
                if debug:
                    print md5hash

                #print self.hashes[md5hash]["type"]
                self.findHashRoute(md5hash)
                ## step through list of known sightings and find route to top-file
                # listhashes = self.hashes[md5hash]
                ##print listhashes
                # sight=listhashes[0]
                # while sight["type"]!="f":
                #    print sight
                #    route.append(sight)
                #    sightlist=self.hashes[sight["in"]]
                #    #print sightlist
                #    sight=sightlist[0]
                # print sight
                # route.append(sight)
                # print "*** Info: route"
                # print route
                # level=0
                # steps = len(route)
                # print "\n***Info: Found a route with %s steps" % steps
                # for i in range(steps):
                #    step = route.pop()
                #    sys.stdout.write(" "*i)
                #    print step["filename"]
                # print "\n"
            pass
        return self.slavesfound

    def findSlave(self, dirname, debug=False, hashing=False, verbose=False):
        '''
        WHDLoad Install archives have no fixed directory structure.
        If there is a dir, it might or might not be called like the archive or basename,
        but might also have hd, -hd, -install, etc. attached, or not. 
        Also there might be no directory in the archive (e.g. alien3 or carcharodon)
        The only real given is that the slave ends in .slave. So that is what this function looks for.
        Input> dirname
        Output> fully qualified filename (where slave is contained)
        '''
        slavesfound = self.findSlaves(dirname, debug, hashing, verbose)

        if len(slavesfound) == 0:
            print "*** Error: no slave found in '%s'\nStop." % dirname
            return
            # sys.exit()

        if len(slavesfound) > 1:
            print "*** Warning: more than one slave found in '%s'. Taking first one.\n%s" % (dirname, slavesfound)

        file = slavesfound[0]
        #self.slavesfound = []  # cleanup

        # double check it is actually a file
        if not os.path.isfile(file):
            print "*** Error: not a file '%s'\nStop." % file
            sys.exit()

        # we are good. lets slice up the result and return the adjusted dir
        if verbose:
            print "Found %s" % file
        return file

    def findSlaveDir(self, dirname, debug=False, hashing=False):
        '''
        WHDLoad Install archives have no fixed directory structure.
        If there is a dir, it might or might not be called like the archive or basename,
        but might also have hd, -hd, -install, etc. attached, or not. 
        Also there might be no directory in the archive (e.g. alien3 or carcharodon)
        The only real given is that the slave ends in .slave. So that is what this function looks for.
        Input> dirname
        Output> adjusted dirname (where slave is contained)
        '''
        file = self.findSlave(dirname=dirname, debug=debug, hashing=hashing)
        if file != None:
            head, tail = os.path.split(file)
            return head
        else:
            return None

    def isManaged(self, entityname, debug=False):
        '''
        returns True if entityname is managed, i.e. a directory exists
        '''
        mandir = assign(self.manageddir)
        if debug:
            print mandir

        category, basename = entityname.split("/")
        if debug:
            print category, basename

        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir, proddir)
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
        # print searchname
        # find right entity
        # try 1: searchname is (category/basename)
        if self.brain["prods"].has_key(searchname):
            if verbose:
                print "Exact match on primary key: %s" % searchname
            entityname = searchname

        else:
            # try : allow capitalization typos, i.e. check lower case
            prodnames = self.brain["prods"].keys()
            foundlower = False
            searchnamelow = searchname.lower()
            for prod in prodnames:
                if searchnamelow == prod.lower():
                    foundlower = True
                    if verbose:
                        print "Match on primary key: %s" % searchname
                    break
            if foundlower:
                entityname = prod
            else:
                # try 3: searchname is basename or name (make sure there is no more than one, as in "Megademo")
                searchnamelow = searchname.lower()
                matched_basenames = []
                matched_names = []
                for key in self.brain["prods"].keys():
                    prod = self.brain["prods"][key]
                    basename = prod["basename"].lower()
                    name = prod["name"].lower()
                    if searchnamelow == basename:
                        matched_basenames.append(key)
                    if searchnamelow == name:
                        matched_names.append(key)
                # check results

                # if 1 matched name, than that is the one
                if len(matched_names) == 1:
                    entityname = matched_names[0]
                    if verbose:
                        print "Match on name: %s" % searchname

                elif len(matched_basenames) == 1:
                    entityname = matched_basenames[0]
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

        mandir = assign(self.manageddir)
        if debug:
            print mandir

        category, basename = entityname.split("/")
        if debug:
            print category, basename

        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir, proddir)
        if debug:
            print proddir, destdir
        if os.path.isdir(destdir):
            if verbose:
                sys.stdout.write(" removing '%s' ... " % entityname)  # destdir
            import shutil
            shutil.rmtree(destdir, ignore_errors=True)
            print "done."
        else:
            print "Hmm, no dir matched the entityname, what happened?"
        return

    def install(self, searchname, debug=False, verbose=False, hashing=False):
        '''
        install a demo/game, getting all required linked images, etc
        returns True on success and False otherwise
        '''
        # !!!
        if hashing and len(self.hashes)==0:
           self.loadHashes()

        # make a local copy of scratchdir to allow modifications
        scratchdir = self.scratchdir

        if True:    # self.isAmiga
            if debug:
                print scratchdir
            if not os.path.isdir(scratchdir):
                # complain and create it
                if verbose:
                    print "Creating my '%s' directory in %s" % (tempwim, assign(self.tempdir))
                os.makedirs(scratchdir)
            else:
                # get rid of previous install junk / CAREFULL!!!
                if True:    #self.isAmiga:
                    self.cleanScratch(scratchdir, verbose)
                else:
                    if verbose:
                        print "Better not delete %s" % scratchdir
                    sys.exit()

        # find right entity
        # try 1: searchname is (category/basename)
        if self.brain["prods"].has_key(searchname):
            if verbose:
                print "Exact match on primary key: %s" % searchname
            entityname = searchname

        else:
            # try : allow capitalization typos, i.e. check lower case
            prodnames = self.brain["prods"].keys()
            foundlower = False
            searchnamelow = searchname.lower()
            for prod in prodnames:
                if searchnamelow == prod.lower():
                    foundlower = True
                    if verbose:
                        print "Match on primary key: %s" % searchname
                    break
            if foundlower:
                entityname = prod
            else:
                # try 3: searchname is basename or name (make sure there is no more than one, as in "Megademo")
                searchnamelow = searchname.lower()
                matched_basenames = []
                matched_names = []
                for key in self.brain["prods"].keys():
                    prod = self.brain["prods"][key]
                    basename = prod["basename"].lower()
                    name = prod["name"].lower()
                    if searchnamelow == basename:
                        matched_basenames.append(key)
                    if searchnamelow == name:
                        matched_names.append(key)
                # check results

                # if 1 matched name, than that is the one
                if len(matched_names) == 1:
                    entityname = matched_names[0]
                    if verbose:
                        print "Match on name: %s" % searchname

                elif len(matched_basenames) == 1:
                    entityname = matched_basenames[0]
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

        #!!! at this point we know exactly what the user wants, i.e. the entityname
        if entityname == "demos/FlyingCows_ProSIAK":
            pass
        data = self.brain["prods"][entityname]
        if verbose:
            print "---> Installing %s by %s (%s)" % (data["name"], data["vendor"], entityname)
            print data
        else:
            # print "%s\n (%s by %s)" % (entityname, data["name"], data["vendor"])
            print "%s" % (entityname)

        # check if this entity is already managed, i.e. a directory category/basename exists
        mandir = assign(self.manageddir)
        basename = data["basename"]
        category = data["category"]
        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir, proddir)
        if os.path.isdir(destdir):
            if verbose:
                print " already exists, skipping"
            return

        # commands=[] # these will be executed one after another on target system
        jobs = joblist("preparations for %s" % data["prodname"], True)

        # make sure to have metadata
        meta = self.getMeta(entityname)
        # if meta["infoparsed"]!= True:
        #    print "*** Info: no parsed info for this"
        # else:
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
            #
        # commands batch 1 (Amiga only), unpack installer
        # unpack installer, with special case for "ctros"
        iname = os.path.join(self.cachedir, "www.whdload.de", data["category"], data["install"])
        # lhaline = "lha e -N %s %s/" % (iname , installdir)
        # commands.append(lhaline)   #!!!
        job1 = unlha(iname, scratchdir, False)
        jobs.addjob(job1)
        # if debug:
        #    print lhaline

        # can only do preparation for this on Amiga
        if False:
            for command in commands:
                os.system(command)
            commands = []

            # find slave, adjust target-dir
            dir = self.findSlaveDir(scratchdir, hashing=hashing)
            if dir != scratchdir:
                if dir == None:
                    return
                if verbose:
                    print "Adjusting installdir to '%s'" % dir
                scratchdir = dir
        else:
            # new code
            jobs.execute() # todo: fix crash bug for "demos/FlyingCows_ProSIAK"
            jobs = joblist("install %s" % data["prodname"], True)
            # find slave, adjust target-dir
            dir = self.findSlaveDir(scratchdir, hashing=hashing)
            if dir != scratchdir:
                if dir == None:
                    return
                if verbose:
                    print "Adjusting installdir to '%s'" % dir
                scratchdir = dir

        category = data["category"]
        # iterate over disks
        if numdisks > 0 or category == "ctros":
            for i in range(numdisks):
                disknum = i + 1
                multiimages = False  # True if more than 1 image per disk
                reqimages = len(images[disknum])
                print "Disk %d requires %d images" % (disknum, reqimages)
                if reqimages > 1:
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
                    print image["seenat"], image["file"]
                url = image["seenat"] + "/" + image["file"]
                if len(image[
                           "file"]) == 0:  # should not be required in the first place, but occured with Faster Than Hell on 18.11.
                    break;
                print "Downloading %s from %s" % (image["file"], url)
                self.tempcache.get(url)

                # handle dms - done
                if type == ".dms":
                    # un-dms with system call
                    fname = os.path.join(assign(self.tempdir), self.tempcache.getpathname(url))
                    adfname = image["file"].lower().replace(image["type"],
                                                            ".adf")  # lower okay as Amiga filesystem is not case sensitive (error found with "r.o.m. 1" which has upper case .DMS)
                    adfnamefull = os.path.join(assign(self.tempdir), adfname)
                    # http://zakalwe.fi/~shd/foss/xdms/xdms.txt
                    # dmsline = "xdms -d %s u %s +%s" % (assign(self.tempdir), fname, adfname)
                    job2 = undms(fname, adfnamefull, False)
                    jobs.addjob(job2)

                    # DIC produces Disk.1/2/3, etc.
                    diskname = "Disk.%s" % disknum
                    targetname = "%s" % (os.path.join(scratchdir, diskname))
                    #print targetname
                    job3 = copy(adfnamefull, targetname, True)
                    jobs.addjob(job3)

                # handle zipped adf - done
                if type == "zip,adf":
                    # fname = os.path.join(self.cachedir, image["file"]) # !!! why was it cachedir, when the download went to temodir?
                    fname = os.path.join(assign(self.tempdir), image["file"])
                    adfname = image["image"]
                    # adfnamefull = os.path.join(assign(self.tempdir), adfname) # was cachedir
                    # -jo for overwrite -no for keeping
                    unzipline = "unzip -jqo %s %s" % (
                    "/%s" % (fname), adfname)  # !!!               e.g. unzip -jqo /cache\katakis.zip katakis.adf
                    # step into tempdir and unzip       # fname= cache\katakis.zip, adfname=katakis.adf adfnamefull=cache\katakis.adf
                    # commands.append("cd %s\n%s" % (assign(self.tempdir),unzipline)) #!!!
                    job2 = unzip("%s" % (fname), assign(self.tempdir), onlynames=[], debug=False)
                    jobs.addjob(job2)

                    # copy adf to installdir
                    # later todo: special case "saveas" for images that need a special name
                    # copyline = 'copy %s/%s to "%s/Disk.%s"' %(assign(self.tempdir), adfname, installdir, disknum) #!!!
                    job3 = copy("%s/%s" % (assign(self.tempdir), adfname), "%s/Disk.%s" % (scratchdir, disknum), True)

                    # commands.append(copyline)  #!!!
                    jobs.addjob(job3)

                # handle adf - done
                if type == ".adf":
                    fname = os.path.join(self.tempdir, image["file"])
                    # adfname = image["file"]
                    # adfnamefull = os.path.join(self.cachedir, adfname)
                    # copy adf to installdir
                    # later todo: special case "saveas" for images that need a special name
                    job2 = copy(fname, "%s/Disk.%s" % (scratchdir, disknum) )
                    jobs.addjob(job2)

                # handle "" and ".exe" (amiga exe that have been downloaded without archive, i.e. also comply to internet url naming)
                if type == "" or type == ".exe":
                    fname = os.path.join(self.cachedir, image["file"])
                    #copyline = 'copy %s to "%s"' % (fname, installdir)
                    #commands.append(copyline)
                    job2 = copy (fname, scratchdir)
                    jobs.addjob(job2)
                    # later todo: special case "saveas" for images that need a special name
                    if image.has_key("copyas"):
                        #renameline = 'cd %s\nrename "%s" "%s"' % (installdir, image["file"], image["copyas"])
                        #commands.append(renameline)
                        job3 = rename("%s/%s"%(scratchdir, image["file"]), "%s/%s"%(scratchdir, image["copyas"]) )
                        jobs.addjob(job3)

                # handle lha
                if type == ".lha":
                    import lhafile
                    print image
                    lhafilename = os.path.join(assign(self.ramtempdir), image["file"])
                    print lhafilename
                    if lhafile.is_lhafile(lhafilename):
                        f = lhafile.Lhafile(lhafilename)
                        flist = []
                        print " listing %s:" % lhafilename
                        for name in f.namelist():
                            print name



        else:
            # typical route for hashes
            # print "*** Info: Data==%s " % data
            route = []
            if hashing == False:
                if len(hashes) > 0:
                    print "*** Info: There is a known hash"
                print "*** Warning: no images found!"
                print "Stop."
                return
                # sys.exit()
            else:
                # try hashing
                print "*** Info: searching via hashes (have %s)" % len(hashes)
                c = 1
                foundHashRoute = False
                bestroute = None
                beststeps = 1985  # arbitrary high number, lower is better
                for h in hashes:
                    print "Try hash %s: %s" % (c, h)
                    c = c + 1
                    route = self.findHashRoute(h)
                    if len(route) > 0:
                        foundHashRoute = True
                        if len(route) < beststeps:
                            beststeps = len(route)
                            bestroute = route
                if not foundHashRoute:
                    print "*** Warning: no hash found a route"
                    # print "Stop."
                    # sys.exit()
                    return
            # here we have a hash route
            level = 0
            steps = len(bestroute)
            print "\n*** Info: Found a route with %s steps" % steps
            for i in range(steps):
                step = bestroute[steps - 1 - i]
                sys.stdout.write(" " * i)
                print step["fullname"]  # was filename
            # empty unnecessary commands from images method
            commands = []
            scratchdir = self.scratchdir
            # get rid of previous install junk / CAREFULL!!!
            # if installdir=="t:temp-wim" and self.isAmiga:
            self.cleanScratch(scratchdir)

            if debug:  # doppelt mit steps==3
                print bestroute
            # unpack with 3 steps
            #arc = "archive:kg/packs"  ## hacked - todo
            #arc = "x:\\amiga\\kg\\packs"
            #arc = assign("PROGDIR:arc")  ## hacked - todo (packs)
            jobs = joblist("hash-install %s" % data["prodname"], False)
            if steps == 3:
                if debug:
                    print bestroute
                zip1 = bestroute[2]["fullname"]  # pack
                zip2 = bestroute[1]["fullname"]  # archive
                #step3line = "unzip -qo %s %s" % ('"%s/%s"' % ((arc, zip1)), zip2)
                #hjb1 = unzip('"%s/%s"' % ((arc, zip1)), zip2)
                #jobs.addjob(hjb1)
                # step into tempdir and unzip zip from containing pack
                #commands.append("cd %s\n%s" % (scratchdir, step3line))
                filename1 = os.path.join(self.arcdir, zip1)
                hjb1 = unzip(filename1, scratchdir, onlynames=[zip2], debug=False)
                jobs.addjob(hjb1)
                # now unzip the extracted archive
                #unzipline = "unzip -qo %s" % (zip2)
                filename2 = os.path.join (scratchdir, zip2)
                hjb2 = unzip(filename2, scratchdir, onlynames=[],debug=False)
                jobs.addjob(hjb2)
                #commands.append("cd %s\n%s" % (scratchdir, unzipline))
            # unpack with 2 steps
            # todo: implement

#            if not self.isAmiga:
#                print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
#                print "Stop."
#                print commands
#                return
#            if debug:
#                print commands
            # unzip it
#            for command in commands:
#                os.system(command)
#            commands = []
            jobs.execute()

            # find slave, adjust target-dir
            dir = self.findSlaveDir(scratchdir, hashing=hashing)
            if dir != scratchdir:
                if dir == None:
                    return
                if verbose:
                    print "Adjusting installdir to '%s'" % dir
                scratchdir = dir
        # if not self.isAmiga:
        #     print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
        #     print "Stop."
        #     return

        # get slave mit lha
        # echo noline "whdload "
        # lha lq -N %s #?.slave >> t:go
        # create go-file

        # !!! todo: put back in
        if False:
            pass
            # old method (use slave name from install archive)
            #     commands.append('echo ";1" >"%s"' % os.path.join(installdir,"go"))
            #     # whdload options
            #     commands.append('echo noline "whdload preload splashdelay=50 quitkey=69 " >>"%s"' % os.path.join(installdir,"go"))
            #     commands.append('lha lq -N %s #?.slave >>"%s"' % (iname, os.path.join(installdir,"go") ))
            #     commands.append('echo "fix" >>"%s"' % os.path.join(installdir,"go"))  # to fix display issues that sometimes occur
        else:
            # new method (use slave name that actually made it to installdir)
            commands = []
            commands.append('echo ";1" >"%s"' % os.path.join(scratchdir, "go"))
            # whdload options
            commands.append(
                'echo noline "whdload preload splashdelay=50 quitkey=69 nocache " >>"%s"' % os.path.join(scratchdir,
                                                                                                         "go"))
            slavefile = self.findSlave(assign(self.ramtempdir), hashing=hashing)
            # print slavefile # lha not unpacked on PC
            head, tail = os.path.split(slavefile)
            commands.append('echo "%s" >>"%s"' % (tail, os.path.join(scratchdir, "go")))
            commands.append(
                'echo "fix" >>"%s"' % os.path.join(scratchdir, "go"))  # to fix display issues that sometimes occur
            #print commands



            # cleanup and show results
            # commands.append('cd %s' %(installdir) ) # don't know how to do renaming of #?.inf to #?.info with AmigaOS, do in Python
            # commands.append('cd "%s"\nlist' % installdir)

            # write extra go-file to tempdir if dir has been adjusted (mind the SELF here!)
            # !!! todo: put back in
            # if self.isAmiga:
            #     if installdir != assign(self.tempdir):
            #         content = ';1\ncd "%s"\nexecute go\n' % installdir
            #         #print content
            #         goname=os.path.join(assign(self.ramptempdir),"go")
            #         h=open(goname, "w")
            #         h.write(content)
            #         h.close()

            # recap
            # if debug:
            #     print "\n--> List of commands:"
            #     for command in commands:
            #         print command

            # go (amiga only)
        #        print "\n--> Performing jobs"
        # if not self.isAmiga:
        #    print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
        #    print "Stop."
        #    return

        # perform action
        jobs.execute()
        # for command in commands:
        #    os.system(command)  # !!!


        # drop a go-file in installdir, i.e. t:\
        slavefile = self.findSlave(assign(self.ramtempdir), hashing=hashing)
        head, tail = os.path.split(slavefile)
        go = ";1\n"
        go += 'whdload preload splashdelay=50 quitkey=69 nocache %s\n' % tail
        # go += "fix\n"
        gofile = open(os.path.join(scratchdir, "go"), "wb")
        gofile.write(go)
        gofile.close()

        # move to managed dir
        if debug:
            print "\nlet's move"
        # 1 - print this dir
        if debug:
            print scratchdir
        # 2 - print managed dir
        mandir = assign(self.manageddir)
        if debug:
            print mandir

        # print entitityname
        basename = data["basename"]  # not sure why this was required, but it contained "vision_megademo" otherwise
        if debug:
            print category, basename
        # 3 - copy stuff over
        import shutil
        proddir = os.path.join(category, basename)
        destdir = os.path.join(mandir, proddir)
        catdir = os.path.join(mandir, category)
        if not os.path.isdir(catdir):
            # only happens on first occasion of demos/mags/ctros/games
            if verbose:
                print "Creating '%s'" % (catdir)
            os.makedirs(catdir)
        shutil.copytree(scratchdir, destdir)
        # 4 only install if basename not in manageddir (done earlier in install)
        # 5 (add remove option)

        return

    def cleanScratch(self, scratchdir, verbose=False):
        if len(os.listdir(scratchdir)) > 0:
            if verbose:
                print "Cleaning scratch-dir '%s'" % scratchdir
            # os.system('cd %s\ndelete #? all force quiet' % installdir)
            import shutil
            shutil.rmtree(scratchdir)
            os.makedirs(scratchdir)


    def hashSlavesInLha(self, install, verbose=False):
        '''
        hash all possible slaves (could be install slaves) in install archive and return as list of md5 hashes
        '''
        hashlist = []
        # check and open lha (using http://trac.neotitans.net/wiki/lhafile)
        lhafilename = os.path.join(self.cachedir, install)
        if lhafile.is_lhafile(lhafilename):
            f = lhafile.Lhafile(lhafilename)
            # find slave filenames
            flist = []
            for name in f.namelist():
                if name.lower().endswith(".slave"):
                    flist.append(name)
            # hash them all
            if len(flist) > 0:
                if verbose:
                    print flist
                for slavename in flist:
                    # s=open((os.path.join(pathname,filename)),"rb").read()
                    m = md5.new()
                    m.update(f.read(slavename))
                    # hashlist.append(m.hexdigest())
                    hashlist.append((install, slavename, base64.urlsafe_b64encode(m.digest())))

                if verbose:
                    print " %s" % hashlist
            else:
                if verbose:
                    print "- no slave found for %s" % install
        return hashlist

    def findInstallMethod(self, content):
        '''
        analyse lha-file for install method (0=RawDIC 1=Patcher 2=DIC 3=Files 4=CD 5=SingleFile)
        :param content: Commodore Amiga installer file candidate
        :return: -1 for unknown/custom, or 0..5 (2=DIC is what we are looking for, really)
        '''

        contentlow = content.lower()
        if contentlow.find("#version") == -1:
            return -1
        lines = contentlow.splitlines()

        # first line sth like: ; $Id: Install 1.11 2006/06/26 09:20:56 wepl Exp wepl $
        if lines[0].find("$id:") == -1:
            return -1
        #todo: isolate and store install version number?

        # (set  #version 2)			;set if no multiple versions 0=RawDIC 1=Patcher 2=DIC 3=Files 4=CD 5=SingleFile
        for line in lines:
            if line.startswith("(set #version "):
                # get rid of ; comments
                #cleanline = line[0:line.find(";")]
                if line.find("(set #version 0)") != -1: # RawDIC
                    return 0
                if line.find("(set #version 1)") != -1: # Patcher
                    return 1
                if line.find("(set #version 2)") != -1: # DIC
                    return 2
                if line.find("(set #version 3)") != -1: # Files
                    return 3
                if line.find("(set #version 4)") != -1: # CD
                    return 4
                if line.find("(set #version 5)") != -1: # Single File
                    return 5
                if line.find("(set #version 6)") != -1: # ARCADIA
                    return 6
                if line.find("(set #version 7)") != -1:
                    return 7
                if line.find("(set #version 8)") != -1:
                    return 8
                if line.find("(set #version 9)") != -1:
                    return 9

        # nothing known found
        return -1

    def printProgress(self, iteration, total, prefix='', suffix='', decimals=2, barLength=100):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : number of decimals in percent complete (Int)
            barLength   - Optional  : character length of bar (Int)
        """
        filledLength = int(round(barLength * iteration / float(total)))
        percents = round(100.00 * (iteration / float(total)), decimals)
        bar = '#' * filledLength + '-' * (barLength - filledLength)
        sys.stdout.write('%s [%s] %d%s %s\r' % (prefix, bar, percents, '%', suffix)),
        sys.stdout.flush()
        if iteration == total:
            print("\n")

    def parseRefsCached(self, debug=False, verbose=False, allow=["demos", "ctros", "mags", "apps", "games"],
                        hashing=False):
        s = self.cache.get(self.url_refs)
        self.parseRefs(s, allow=allow, debug=False, verbose=verbose, hashing=hashing)
        self.saveDict()

    def parseRefs(self, string, debug=False, verbose=False, allow=["demos", "ctros", "mags", "apps", "games"],
                  hashing=False):
        lines = string.splitlines()

        iscommentblocks = False  # True while scanning comment lines
        lastlinewascomment = False  # non-commment lines will trigger a new block
        numcommentblocks = 0  # counter for simple check
        hadplaceholder = False  # placeholder-block between first and second comment
        placeholderdone = False  # True after placeholder-block has been done, allows for speedup with real data

        # parsing currently only works on pc (some formatting issues)
        if self.isAmiga:
            print "*** Error: reference parsing currently does not work on Amiga\nStop."
            sys.exit()

        # get corrections.dict handy
        corrections = eval(open("data/corrections.dict").read())
        print "loaded corrections.dict"  #: %s" %corrections
        maxcount =  len(lines)
        count=0
        for line in lines:
            line = line.decode("latin1")
            #sys.stdout.write ("\r%s" % line)
            self.printProgress(count,maxcount,prefix = 'Parsing references:', suffix = 'Complete', barLength = 50)
            count += 1
            has_corrections = False  # does not mean the file, but will be True is an entity like "Arte" has corrections
            if line.startswith("#"):
                # comments
                if lastlinewascomment == False:
                    iscommentblocks = True
                    lastlinewascomment = True
                    # when placeholders are done, we only expect comment and data-lines
                    if hadplaceholder:
                        placeholderdone = True
                if debug:
                    print line
            else:
                if lastlinewascomment:
                    # notice block changes from comment to data
                    numcommentblocks += 1
                    lastlinewascomment = False

                # data-line
                if not placeholderdone:
                    # placeholder/assign block
                    elems = line.split(":=")
                    if debug:
                        print elems, len(elems)
                    if len(elems) != 2:
                        print "*** Warning: unknown line-format: %s" % line
                        break
                    else:
                        # this is a placeholder line with ":=", e.g. "whdload:=http://www.whdload.de/whdload/images/"
                        hadplaceholder = True
                        self.placeholder[elems[0]] = elems[1]  # assign placeholder to dictionary
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
                    elems = line.split("#")
                    if len(elems) != 11:
                        print "*** Warning: line has %d instead of 11 elements: %s" % (len(elems), line)
                    else:
                        category = elems[0]
                        basename = elems[1]  # is together with category the primary key
                        name = elems[2]  # multiple names separated with '*'
                        vendor = elems[3]
                        iauthor = elems[4]  # multiple separated with ','
                        images = elems[5]  # multiple separated with ','
                        id_hol = elems[6]
                        id_lemon = elems[7]
                        id_bitworld = elems[8]
                        id_ada = elems[9]
                        id_pouet = elems[10]

                        # apply corrections, step 1
                        if corrections.has_key((category, basename)):
                            has_corrections = True

                        # store entity meta (demos only atm)
                        # if category == "demos":
                        if (category in allow):  # and has_image: #after applied corrections
                            install = basename + ".lha"
                            info = basename + ".html"
                            path_install = category + "/" + install
                            path_info = category + "/" + info
                            url_install = urlparse.urljoin(self.url_whdload, path_install)
                            url_info = urlparse.urljoin(self.url_whdload, path_info)
                            # url=os.path.join(self.url_whdload,category,install)

                            # get lha-file to cache
                            s = self.cache.get(url_install)  # got cached lha

                            prodname = name

                            # fill meta data structure
                            meta = {}
                            meta["category"] = category
                            meta["basename"] = basename
                            # construct primary key in a commandline-friendly fashion
                            primary = "%s/%s" % (category, basename)

                            meta["prodname"] = prodname
                            meta["name"] = name
                            meta["vendor"] = vendor
                            meta["iauthor"] = iauthor
                            meta["oimages"] = images
                            meta["id_hol"] = id_hol
                            meta["id_lemon"] = id_lemon
                            meta["id_bitworld"] = id_bitworld
                            meta["id_ada"] = id_ada
                            meta["id_pouet"] = id_pouet

                            meta["fromindex"] = "refs.txt"
                            meta["info"] = info
                            meta["install"] = install
                            meta["infoparsed"] = False

                            # get list of possible install files
                            filename = self.cache.getfilename(url_install)
                            installmethod=None
                            if lhafile.is_lhafile(filename):
                                l = lhafile.Lhafile(filename)
                                namelist = l.namelist()
                                installlist = []
                                for iname in namelist:
                                    if os.path.basename(iname.lower()).find("install") != -1:
                                        if iname.lower().find(".info") == -1:
                                            installlist.append(iname)
                                for iname in installlist:
                                    content = l.read(iname)
                                    installmethod = self.findInstallMethod(content)
                                    if installmethod != -1:
                                        break
                            else:
                                # todo: possibly delete file from cache, as it is not lha (might be transmission error)
                                pass
                            meta["installmethod"] = installmethod
                            methodstring="install%s" % installmethod
                            self.dh.logValueToDict(self.errors, methodstring, primary)

                            #if installmethod != None:
                            #    print "  ** Installmethod: %s" % installmethod


                            # apply corrections step 2
                            touchedimages = False
                            if has_corrections:
                                if verbose:
                                    print "  applying corrections for %s (%s), i.e. %s" % (
                                    basename, category, corrections[(category, basename)].keys())
                                for key in corrections[(category, basename)].keys():
                                    if key == "images":
                                        touchedimages = True
                                        # if debug:
                                        #    print "touched %s of %s" % (key,name)
                                        # sys.exit()
                                    # this worked great up to v0.11, but caused a lot of boiler plate when dealing e.g. with "copyas"
                                    meta[key] = corrections[(category, basename)][key]

                                    # therefore try a more clever approach with dict copy, one day ;)
                                    # meta[key]=corrections[(category,basename)][key]

                                meta["fromindex"] = "corrections.dict"

                            if not touchedimages:
                                # print images
                                images = self.buildImagesMeta(prodname, images, debug=self.debug, verbose=self.verbose,
                                                              primary=primary)
                                # set images and consider special case for "ctros"
                                if category != "ctros":
                                    meta["images"] = images
                                else:
                                    meta["images"] = None
                            touchedimages = False

                            # hash slaves if hashing enables
                            hashlist = []
                            if hashing:
                                # check and open lha (using http://trac.neotitans.net/wiki/lhafile)
                                hashlist = self.hashSlavesInLha(install)
                                # lhafilename = os.path.join("cache", install)
                                # if lhafile.is_lhafile(lhafilename):
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
                                listOfOldInstallArchives = self.getOldInstalls(install,
                                                                               url_info)  # got cached html info
                                # get tail of each href
                                oldinstalls = []
                                for href in listOfOldInstallArchives:
                                    head, oldinstall = os.path.split(href)
                                    print "    hashing: %s" % oldinstall
                                    oldinstalls.append(oldinstall)
                                    hashlist.extend(self.hashSlavesInLha(oldinstall))

                                    # print listOfOldInstallArchives

                            # save to seperate dict
                            meta["md5"] = hashlist

                            # if name=="Arte":
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
                            has_corrections = False  # reset for next loop

                            # save precious debugging time by reducing turn around with lots of http connections
                            if debug:
                                self.saveDict()

                                # else:
                                #    #if debug:
                                #    print "*** Warning: cleaning due to missing images: %s (%s)" % (prodname,meta["images"])
                                # if debug:
                                #    if prodname == "Roots":
                                #        print meta

                        else:
                            if debug:
                                # print "*** Skipping: %s" % name
                                pass

        if debug:
            print "\n\nnumcommentblocks: %d" % numcommentblocks
            # print "\nplaceholders= %s" % self.placeholder
            print "\ncategories: %s" % self.brain["stats"]["category"]
            # print "\nvendors: %s" % self.stat_vendor # could be used to list by group/vendor
            # print "\nimage authors: %s" % self.stat_iauthor

    def getOldInstalls(self, install, url_info, debug=False):
        '''
        investigate supplied url for linked "old install" lha archives of the install.
        get a local copy of each of them and return list of names (ready to be stored as "installs_old")
        '''
        # if debug:
        print install, url_info
        s = self.cache.get(url_info)
        # print url_info
        # if url_info =="http://www.whdload.de/games/1943.html":
        hrefs = []
        if s.find("Old Install Archives") != -1:
            w = BeautifulSoup(s, "html.parser")
            # get list of all hrefs referring to ".lha"
            # lhas = w.find_all(href=re.compile(".lha"))
            th = w.find("th", text=re.compile("Old Install"))
            if th != None:
                if debug:
                    print th
                tr = th.parent
                if tr != None:
                    if debug:
                        print tr
                    table = tr.parent
                    if debug:
                        print table

                    if table != None:
                        lhas = table.find_all("a", href=re.compile(".lha"))
                        if debug:
                            print "found %d entries" % (len(lhas))
                            print lhas
                            print
                            print url_info

                        # iterate over list and store old hrefs
                        for a in lhas:
                            href = a["href"]
                            # print href
                            if debug:
                                print href
                            if href != install:
                                fullhref = urllib.basejoin(url_info, href)
                                hrefs.append(fullhref)

                        if debug:
                            print
                            print hrefs

                        # get a local copy of all of them
                        for href in hrefs:
                            print "  downloading old install: '%s'" % href
                            self.cache.get(href)

                            # print install
        else:
            pass
            # print "*** Info: no old installs"
            # sys.exit()
        return hrefs

    def cleanRefsCached(self, debug=True, verbose=False, hashing=False):
        '''
        removes all entities without images, recalc stats and saves the brain-file
        new in 2016: remove unsupported install methods as well
        '''
        # step over all prods
        # print "---> Cleaning"
        # self.getStats()
        newdict = {}
        newdict["prods"] = {}
        newdict["stats"] = {}

        # dicts for stats, filled by parseRefs, reachable from getStats()
        newdict["stats"]["category"] = {}
        newdict["stats"]["vendor"] = {}
        newdict["stats"]["iauthor"] = {}

        for name in self.brain["prods"]:
            # print self.brain["prods"][name]
            # print name
            # if len( str(self.brain["prods"][name]["images"]) )>2 or name=="games/Unreal" or (hashing and len(self.brain["prods"][name]["md5"])>0):
            if len(str(self.brain["prods"][name]["images"])) > 2 or (
                hashing and len(self.brain["prods"][name]["md5"]) > 0): #\
                    #or self.brain["prods"][name]["installmethod"]==2:
                # quick check okay, i.e. more than "{}"
                # copy over entry
                # print "keep %s" % name
                newdict["prods"][name] = self.brain["prods"][name]
                # print self.brain["prods"][name]["category"]
                self.dh.countToDict(newdict["stats"]["category"], self.brain["prods"][name]["category"])
                self.dh.countToDict(newdict["stats"]["vendor"], self.brain["prods"][name]["vendor"])
                self.dh.countToDict(newdict["stats"]["iauthor"], self.brain["prods"][name]["iauthor"])
            else:
                # remove this prod from brain, i.e. do not copy
                # print "remove %s" %name
                # sys.exit()
                self.dh.logValueToDict(self.errors, "cleaned", name)
                if verbose:
                    print "remove %s (%s)" % (name, self.brain["prods"][name]["images"])
                pass

        # set newdict as brain
        # self.brain = newdict # too much, be more subtle
        numwas = len(self.brain["prods"])
        numis = len(newdict["prods"])
        diff = numwas - numis

        print "Cleaning removed %s productions without images from brain-file (from %s to %s)" % (diff, numwas, numis)
        if diff != 0:
            print "  old brain contained %s vendors in %s categories %s" % (
            len(self.brain["stats"]["vendor"]), len(self.brain["stats"]["category"]), self.brain["stats"]["category"])
            print "  new brain contains %s vendors in %s categories %s" % (
            len(newdict["stats"]["vendor"]), len(newdict["stats"]["category"]), newdict["stats"]["category"])
        else:
            print "  brain contains %s vendors in %s categories %s" % (
            len(newdict["stats"]["vendor"]), len(newdict["stats"]["category"]), newdict["stats"]["category"])

        self.brain["prods"] = newdict["prods"]
        self.brain["stats"] = newdict["stats"]

        # self.getStats()
        self.saveDict()

import zipfile
import cStringIO as StringIO
# import lhafile (only pc c-extension, but like zipfile)
import md5
import os,sys, time
import base64 # looking for shorter filenames as of http://effbot.org/librarybook/md5.htm


class whdloadhasher:
    # derived from hasher2.py on 08.06.2017
    config = {}

    def __init__(self, config={}):
        self.config = config  # put a wim.py config here
        # !!! init stuff moved here to maintain self
        self.arcdir = config["arcdir"]
        self.dh = wicked.helpers.dicthelpers()
        try:
            self.hashes = self.dh.loadDictionary("data/brain-hashes.dict")
        except:
            self.hashes = {}

    def md5hexfile(self, filename):
        # s=open((os.path.join(pathname,filename)),"rb").read()
        s = open(filename, "rb").read()
        m = md5.new()
        m.update(s)
        # searchhash = m.hexdigest()
        searchhash = base64.urlsafe_b64encode(m.digest())
        return searchhash

    def isknownfilename(self, filename):
        '''
        returns True if filename is already used in a hash
        '''
        keys = self.hashes.keys()
        # print keys
        # print len(keys)
        for key in keys:
            # its a list
            elems = self.hashes[key]
            for elem in elems:
                # print elem
                if elem["type"] == "f":  # is file
                    if elem["filename"] == filename:
                        return True
        return False

    def findhash(self, filename):
        '''
        returns hash for known filenames
        '''
        keys = self.hashes.keys()
        for key in keys:
            # its a list
            elems = self.hashes[key]
            for elem in elems:
                if elem["type"] == "f":  # is file
                    if elem["filename"] == filename:
                        return key
        return ""

    def analyzeZIP(self, filehandle, container="", filename=""):
        '''
        prior to Python v2.7 only filename
        http://docs.python.org/2/library/zipfile
        take in an open file-handle (e.g. from open or zipfile.open) and return True if it is ZIP
        '''
        # print filehandle
        if zipfile.is_zipfile(filehandle):
            z = zipfile.ZipFile(filehandle)
            for info in z.infolist():
                # get filename
                zfilename = info.filename
                # print zfilename

                # recurse if filename ends on .zip
                if zfilename.lower().endswith(".zip"):
                    print " recursing into '%s'" % zfilename
                    # analyzeZIP(z.open(zfilename, "r"),container=container, filename=zfilename)
                    i = z.getinfo(zfilename)
                    # print i.date_time
                    # print i.filename
                    # print i.compress_type
                    # print i.comment
                    # print i.extra
                    # print i.create_system
                    # print i.create_version
                    # print i.extract_version
                    # print i.reserved
                    # print i.flag_bits
                    # print i.volume
                    # print i.internal_attr
                    # print i.external_attr
                    # print i.header_offset
                    # print i.CRC
                    # print i.compress_size
                    # print i.file_size
                    # print " created %s, original size: %s, compressed size: %s, ratio: %.2f %%" % (i.date_time, i.file_size, i.compress_size, float(i.compress_size)/ float(i.file_size)*100)

                    # load file with stringio
                    memfile = StringIO.StringIO()
                    memfile.write(z.read(zfilename))
                    memfile.seek(0)

                    # md5 hash the containing file
                    m = md5.new()
                    m.update(memfile.read())
                    # ziphash = m.hexdigest()
                    ziphash = base64.urlsafe_b64encode(m.digest())
                    hi = {}
                    hi["fullname"] = zfilename
                    head, tail = os.path.split(zfilename)
                    hi["filename"] = tail
                    hi["type"] = "z"  # in zip
                    hi["in"] = container
                    self.dh.logValueToDict(self.hashes, ziphash, hi)

                    # step into containing file
                    memfile.seek(0)
                    self.analyzeZIP(memfile, container=ziphash, filename=zfilename)
                    print "******************************"
                # compute md5 hash if filename ends on .slave
                if zfilename.lower().endswith(".slave"):
                    s = z.read(zfilename)
                    m = md5.new()
                    m.update(s)
                    # zfilehash = m.hexdigest()
                    zfilehash = base64.urlsafe_b64encode(m.digest())
                    print " file: %s, md5: %s" % (zfilename, zfilehash)
                    # if zfilehash==searchhash:
                    #    print "*** Info: Matching MD5 sum for searchhash '%s' on file '%s'" % (searchhash, zfilename)
                    #    #sys.exit()
                    # store has info for this file
                    hi = {}
                    hi["fullname"] = zfilename
                    head, tail = os.path.split(zfilename)
                    hi["filename"] = tail
                    hi["in"] = container  # hash of
                    hi["type"] = "z"  # zip

                    # hashes[zfilehash]=hi
                    self.dh.logValueToDict(self.hashes, zfilehash, hi)
                else:
                    pass  # print " file: %s" % (zfilename)
        else:
            print "*** Error: not a ZIP-File: '%s'" % filename

    def hasharchives(self):
        # main method, configure via config dict passed during instantion

        filenames = os.listdir(self.arcdir)
        # info
        print "Hashing archives in directory '%s' ..." % self.arcdir

        # iterate over filenames in filesystem to start with (later recurse in archives as well)
        for filename in filenames:
            fullfilename = os.path.join(self.arcdir, filename)
            print fullfilename
            filehandle = open(fullfilename, "rb")
            if zipfile.is_zipfile(filehandle):
                sys.stdout.write("*** Info: ZIP-file '%s', " % fullfilename)
                if self.isknownfilename(filename):
                    print "is known"
                    ziphash = self.findhash(filename)
                else:
                    ziphash = self.md5hexfile(fullfilename)
                    hi = {}
                    hi["fullname"] = filename
                    head, tail = os.path.split(filename)
                    hi["filename"] = tail
                    hi["type"] = "f"  # file

                    # hashes[ziphash] = hi
                    self.dh.logValueToDict(self.hashes, ziphash, hi)

                    print " md5: %s" % (ziphash)

                    # open file and analyze
                    self.analyzeZIP(filehandle, container=ziphash, filename=filename)
            else:
                pass
                # print "*** Warning: not a zip-file: %s ... skipping" % fullfilename

        self.dh.saveDictionary(self.hashes, "data/brain-hashes.dict")