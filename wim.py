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
#          - setVariables() for debug and verbose stats, linked to -v option
#          - stats of failure sources in buildimagesmeta. check with "wim.py -rvc"
#          - changed primarykey from str(name) to str((category, basename)), uncovering lots of megademos
#          - improved install() do be more clever with searchname matching (e.g. Arte, Sanity_Arte, ('demos', 'Sanity_Arte')) all pass, and Megademo lists matching megademos
#          - made basename and name search lowercase
# 22.10.13 - lowercase search for primary key in install()


# done>

# todo:
#       - autodetect rawdic/dic install (find "(set #program "DIC")" , or "(set #program "RawDIC")" in install)

#     - devise switch for different install methods
#       - make Katakis work (1 disk adf in zip advanced case)
#       - make desert dreams work (2 disk simple dms)

#       - seperate function for building stats
#       - fix stats upon recreation

#       - create dirs as needed, unpack there, support removing (otherwise no package manager)
#       - patch .dm typo for Megademo Excellence (what is the correct name for the patch list)
#       - fix error line 723 in cleanRefsCached (self.dh.countToDict(self.errors,"removed for missing images '%s'" % self.brain["prods"][name]["images"]))
#       - make lha work
#       - make lzx work
#       - make zip work
#       - make adf work

#       - -x for execute option

#       - use md5 or other hash to verify and find disk images
#       -- seen as in hash
#       - help verify / install the right software (lha, lzx, rawdic, dic, patcher, installer, quite a list :)

#       - investigate python lha depacking (e.g. http://trac.neotitans.net/wiki/lhafile or http://code.google.com/p/python-libarchive/)
#       -- lhafile install: SET VS90COMNTOOLS=%VS100COMNTOOLS%, easy_install http://svn.neotitans.net/lhafile/ works on pc!


import os,sys,getopt,time
try:
    import cPickle as pickle
except:
    import pickle
from lxo_helpers import dicthelpers


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

try:
    from bs4 import BeautifulSoup
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

class whdloadProxy:

    #url_all= "http://www.whdload.de/demos/all.html"
    #url_allv = "http://www.whdload.de/demos/allv.html"
    #url_path = "http://www.whdload.de/demos/" # deprecated since 0.04

    url_whdload = "http://www.whdload.de/"
    url_refs = "http://whdload.de/db/refs.txt"
    placeholder={}

    cachedir = "cache"
    #amidisk = "ff0:"
    tempdir = "t:"
    isAmiga = -1
    
    lastt = None
    
    #prods = {}  # results will go here
    brain = {}  # results will go here
    dh=None
    
    debug=False
    verbose=False
    errors={}
    
    def __init__(self):
        t1=time.clock()
        self.dh=dicthelpers()
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
        return
        
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
        #try:
        #    self.prods=dh.loadDictionary("wimpy.dict")
        #except:
        #    print "*** Error: Can't load 'prods.dict'. Run this on Windows first!"
    
    def cacheGet(self, url):
        '''
        Gets content from a URL and drops a copy in cachedir. Will use content from the cached file from then on.
        
        Limitations:
        - Currently does not handle multiple basenames from different URLs
        
        Returns a string
        '''
               
        # get basename (last component) and construct local filename
        basename = os.path.basename(url)
        filename = os.path.join(self.cachedir,basename)
        
        # strategy 1: try getting a cached copy and return
        if os.path.exists(filename):
            # open the existing file
            file=open(filename)
            if file:
                content = file.read()
                file.close()
                return content
            
        # strategy 2: try getting the url, drop a cached binary copy, and return the content
        content = urllib.urlopen(url).read()
        savefile = open(filename, "wb")
        savefile.write(content)
        savefile.close()
                
        return content    
    
    def expandPlaceholders(self, url, debug=False):
        '''
        uses self.placeholder to expand url to original state
        '''
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
        
    def buildImagesMeta(self, demo, hint, debug=False, verbose=True, allow=[".dms"]):
        '''
        consume non deterministic pointer to images and try to be clever about it
        input: last entry from the line from the list of installs
        out dictionary with 
        '''
        # quick out if images is already a dict not a str
        if type(hint)=="dict":
            return hint # means that it was most probably already fixed or corrected
        
        #if demo=="Roots":
        if True:
            #print "--> parsing image locations"
            # one disks first, start with dms
            
            # get basename
            seenat, filename = os.path.split(hint)
            seenat = self.expandPlaceholders(seenat)
            if len(filename)==0:
                self.dh.countToDict(self.errors,"no direct link")
                if verbose:
                    print "*** Warning: no direct link to: %s (%s)" % (demo,hint)
                return {}
            # get suffix
            trash, ext = os.path.splitext(hint)
            ext=ext.lower()

            if len(ext)==0:
                self.dh.countToDict(self.errors,"no direct link")
                if verbose:
                    print "*** Warning: no direct link to: %s (%s)" % (demo,hint)
                return {}

            
            # check for allowed extensions
            if ext not in allow:
                self.dh.countToDict(self.errors,"unsupported extension '%s'" % ext)
                if verbose:
                    print "*** Warning: unsupported extension '%s' for '%s' ('%s','%s')" % (ext,demo,hint,seenat)
            
            if debug:
                print demo, seenat, filename, ext
            
            # only dms for the moment
            if ext!= ".dms":
                return {}
            
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
        #s = self.cacheGet(self.url_path + self.brain["prods"][demoname]["info"])
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
        prints all currently known and supported entitites of a certain category. prints all it category is ""
        '''
        if category=="":
            p=True
        else:
            p=False
        for prod in self.brain["prods"].keys():
            if p or self.brain["prods"][prod]["category"]==category:
                print "%s by %s" % (self.brain["prods"][prod]["prodname"], self.brain["prods"][prod]["vendor"])
    def getStats(self):
        '''
        print some stats from parseRefs

        self.stat_category={}
        self.stat_vendor={}
        self.stat_iauthor={}

        '''
        print "Common errors: %s" % str(self.errors)
        print "\nKnown categories: %s" % str(self.brain["stats"]["category"])
        
    
    def buildTables(self, recursive=False, debug=False):
        '''
        Cache relevant content and parse demo list
        '''
        #self.parseIndexAll(recursive=recursive, debug=False)
        #self.parseIndexAllV(recursive=recursive, debug=False)
        self.parseRefsCached()
          
    def install(self, searchname, debug=False, verbose=False):
        '''
        install a demo, getting all required linked images, etc
        currently works with .dms 1 disk 1 image only
        returns True on success and False otherwise
        '''
        
        # find right entity
        # try 1: searchname is (category/basename)
        if self.brain["prods"].has_key(searchname):
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
                    print "Match on name: %s" % searchname

                elif len(matched_basenames)==1:
                    entityname=matched_basenames[0]
                    print "Match on basename: %s" % searchname

                else:
                    print "*** Error: your searchname '%s' yielded no exact match:" % searchname
                    print "on primary key: []"
                    print "on basenames: %s" % matched_basenames
                    print "on names: %s" % matched_names
                    print "Stop."
                    sys.exit()             
        
        data = self.brain["prods"][entityname]
        print "---> Installing %s by %s" % (data["name"], data["vendor"])

        commands=[] # these will be executed one after another on target system

        # make sure to have metadata
        meta = self.getMeta(entityname)
        if meta["infoparsed"]!= True:
            print "*** Warning: no parsed info for this"

        '''
        {'info': 'Sanity_NotAgain.html', 'prodname': u'Not Again', 'infoparsed': True, 'fromindex': 'all.html', 'groupname':
'?', 'install': 'Sanity_NotAgain.lha',
'images': {1: [{'seenat': 'http://www.aminet.net/demo/mega', 'type': '.dms', 'file': 'notagain.dms'}]}}
'''
        images = data["images"]
        if debug:
            print images
        # number of disks
        numdisks = len(images)
        if debug:
            print "Number of disks: %d" % numdisks

        # iterate over disks
        if numdisks>0:
            for i in range(numdisks):
                disknum=i+1
                reqimages = len(images[disknum])
                print "Disk %d requires %d images" % (disknum, reqimages)
                if reqimages >1:
                    print "*** Error: Cannot currently handle the case of multiple images per disk"
                    return False
                image = images[disknum][0]
                
                # check for dms
                if image["type"]!=".dms":
                    print "*** Error: Cannot currently handle anything else than .dms"
                    return False
                print image
                
                # get file
                if debug: 
                    print image["seenat"],image["file"]
                url = image["seenat"]+"/"+image["file"]
                print "Trying to get %s from %s" % (image["file"], url)
                self.cacheGet(url)
                
                # un-dms with system call
                fname = os.path.join(self.cachedir, image["file"])
                #dmsline = "dms write %s to %s" % (fname, self.amidisk)
                # http://zakalwe.fi/~shd/foss/xdms/xdms.txt
                adfname = image["file"].lower().replace(image["type"],".adf")    #lower okay as Amiga filesystem is not case sensitive (error found with "r.o.m. 1" which has upper case .DMS)
                adfnamefull = os.path.join(self.cachedir, adfname)
                dmsline = "xdms -d %s u %s +%s" % (self.cachedir, fname,adfname)
                if debug:
                    print "Creating %s from %s" %(adfnamefull, fname)
    
                #os.system(dmsline)
                commands.append(dmsline)
        else:
            print "*** Error: no disks found!"
            print data
            sys.exit()
                      
        # unpack installer
        iname = os.path.join(self.cachedir, data["install"])
        #lhaline = "lha x -N %s %s" % (iname ,self.tempdir)
        lhaline = "lha e -x0 -N %s #?.inf #?.slave #?README %s" % (iname ,self.tempdir)
        #lhaline = "lha e -x0 -N %s #?.slave #?README %s" % (iname ,self.tempdir) # no inf
        commands.append(lhaline)

        # ab hier wirds h?sslich hardcoded zum ende des tages :)
        # hardcoded for Sanity
        #commands.append('cd "t:NotAgain Install"')
        
        # DIC produces Disk.1
        copyline = 'copy %s/%s to "t:Disk.1"' %(self.cachedir, adfname)        
        commands.append(copyline)
        #commands.append('list "t:NotAgain Install/"')
        
        # get slave mit lha
        # echo noline "whdload "
        # lha lq -N %s #?.slave >> t:go
        commands.append('echo ";1" >t:go')
        commands.append('echo noline "whdload " >>t:go')
        commands.append('lha lq -N %s #?.slave >> t:go' % iname)

        #commands.append('cd "t:NotAgain Install/"')
        #commands.append('rename "t:NotAgain.inf" "t:NotAgain.info"')
        #commands.append('list "t:"')
        commands.append('cd t:')
        #commands.append('cd "t:"\nwhdload Notagain.slave')      

        # recap
        print "\n--> List of commands:"
        for command in commands:
            print command
        
        # go (amiga only)
#        print "\n--> Performing jobs"
        if not self.isAmiga:
           print "*** Warning: Not running on Amiga, but installation commands are Amiga OS specific. (Run the same script inside Amiga.)"
           print "Stop."
           return

        for command in commands:
            os.system(command)
            
        
        return

    def parseRefsCached(self,allow=["demos","ctros","mags","apps","games"]):
        s = self.cacheGet(self.url_refs)
        self.parseRefs(s,allow=allow)
        self.saveDict()

    def parseRefs(self, string, debug=False, allow=["demos","ctros","mags","apps"]):
        lines = string.splitlines()
        
        iscommentblocks=False       # True while scanning comment lines
        lastlinewascomment=False    # non-commment lines will trigger a new block
        numcommentblocks=0          # counter for simple check
        hadplaceholder=False        # placeholder-block between first and second comment
        placeholderdone=False       # True after placeholder-block has been done, allows for speedup with real data
        
        # get corrections.dict handy
        corrections=eval(open("corrections.dict").read())
        print "loaded corrections.dict: %s" %corrections      
        
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
                            path = category+"/"+install
                            url=urlparse.urljoin(self.url_whdload,path)
                            #url=os.path.join(self.url_whdload,category,install)
                            s= self.cacheGet(url)
                            #print "downloading: %s" %url
                                               
                            prodname = name
                            
                            # fill meta data structure
                            meta = {}
                            meta["category"]=category
                            meta["basename"]=basename
                            meta["prodname"]=prodname
                            meta["name"]=name
                            meta["vendor"]=vendor
                            meta["iauthor"]=iauthor
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
                                print "*** Info: applying corrections for %s (%s), i.e. %s" %(basename, category, corrections[(category,basename)].keys())
                                for key in corrections[(category,basename)].keys():
                                    if key=="images":
                                        touchedimages=True
                                        print "touched %s of %s" % (key,name)
                                        #sys.exit()
                                    meta[key]=corrections[(category,basename)][key]
                                    print meta[key]
                                meta["fromindex"]="corrections.dict"
                            
                            if not touchedimages:
                                #print images
                                images = self.buildImagesMeta(prodname, images,debug=self.debug,verbose=self.verbose)
                                meta["images"]=images
                            touchedimages=False
                            
                            if name=="Arte":
                                print meta
                            if has_corrections:
                                print meta
                                print
                            
                            has_corrections=False   # reset for next loop

                                
                            # should be moved to after applied corrections!
                            #if len(images)!=0:
                            #    has_image = True
                            #else:
                            #    has_image = False
                        
                            #if category == "demos":
                            #    if not has_image and debug:
                            #        print "*** Warning: no images for: %s" % name
                            #    #else:
                            #        #if name == "Roots":
                            #        #    print line
                            #        #    print "category: %s\nbasename: %s\nname: %s\nvendor: %s\niauthor: %s\nimages: %s\nid_hol: %s\nid_lemon: %s\nid_bitworld: %s\nid_ada: %s\nid_pouet: %s" %(category, basename, name, vendor, iauthor, images, id_hol, id_lemon, id_bitworld, id_ada, id_pouet)
                            #if category == "games":
                            #    if len(images)!=0:
                            #        #print "*** Wow: images for: %s" % name
                            #        pass        
                            # quick hack
                            #if len(str(meta["images"]))>2:   #{}
                            
                            # construct primary key in a commandline-friendly fashion
                            primary = "%s/%s" % (category, basename)
                            
                            self.brain["prods"][primary] = meta
                            # count some stats (todo: avoid double counting -> seperate function)
                            self.dh.countToDict(self.brain["stats"]["category"], category)
                            self.dh.countToDict(self.brain["stats"]["vendor"], vendor)
                            self.dh.countToDict(self.brain["stats"]["iauthor"], iauthor)
                        
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
                
    def cleanRefsCached(self, debug=True,verbose=False):
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
            if len( str(self.brain["prods"][name]["images"]) )>2:
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
                self.dh.countToDict(self.errors,"missing images")
                if verbose:
                    print "remove %s (%s)" % (name,self.brain["prods"][name]["images"])
                pass
        
        # set newdict as brain
        self.brain = newdict
        self.getStats()
        self.saveDict()
        

def test(demo,debug=False,verbose=True):
    #has = demos.hasDemo(demo)
    #print "has: %s" % has
    print
    if debug:
        print "%s, %s" % (demo, has)
    #if has:
    if verbose:
        print "  %s" % demos.getMeta(demo, debug=debug)
    # try to install
    demos.install(demo, debug=debug, verbose=verbose)
        
def test2():
    self.parseRefsCached()
    self.saveDict()

#---get the arguments
print "Wim.py v0.07, WHDLoad Install Manager by Leif Oppermann (20.10.2013)"
#print "  automates your WHDLoad installation chores"

optlist, args = getopt.getopt(sys.argv[1:],'i:vl:bcrs')
if len(optlist)==0:
    print "what to do?"
    sys.exit()
 
#print optlist, args       

# instantiate
demos = whdloadProxy()

for o, a in optlist:
    print o, a

    if o== "-r":
        print "  parseRefs()"
        have_r=True
        #demos.parseRefsCached()

    if o== "-c":
        print "  cleanRefs()"
        have_c=True
        #demos.cleanRefsCached()

    if o== "-l":
        print "  list known %s" % a
        have_l = True
        #demos.getKnownEntities(a)
        #sys.exit()

    if o== "-s":
        have_s=True
        #print "  list stats" % a
        #demos.getStats()
        #sys.exit()

    if o == "-v":
        print "  verbose"
        g_debug=True
        g_verbose=True
        demos.setVariables(debug=g_debug, verbose=g_verbose)

    if o == "-b":
        print "  build tables"
        have_b = True
        #demos.buildTables(recursive=True)
        #sys.exit()

    #if o == "-t":
        ##print "  install: %s" % a
        #demos.getStats()

    if o == "-i":
        have_i=True
        #print "  install: %s" % a
        #test(a,debug=False,verbose=False)
        
    #    if o == "-c":
    #print "  capabilities are: 'urllib'-%s, 'bs4'-%s" % (q(config["has_urllib"],"True","False"), q(config["has_bs4"],"True","False"))


# execute actions
if have_r:
    print "\n---> Parsing References"
    demos.parseRefsCached()
if have_b:
    print "\n---> Building Tables"
    demos.buildTables(recursive=True)
    sys.exit()

#todo: whats the difference between r and b?

if have_c:
    print "\n---> Cleaning"
    demos.cleanRefsCached()

if have_s:
    print "\n---> Stats"
    demos.getStats()

if have_l:
    print "\n---> list"
    demos.getKnownEntities(a)
    sys.exit()

if have_i:
    #print "\n---> Installing"
    test(a,debug=False,verbose=False)

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






