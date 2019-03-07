#!/usr/bin/env python
# 10.10.13 - first test on WHDLoad Installer with BeautifulSoup HTML parsing
# 12.10.13 - second version, put into class, cacheGet, build tables from all.html, hasDemo, getMeta
# 13.10.13 - made to work on amiga python 2.0 and pc python 2.7, stored local dict, called wimpy
#          - started using komodo ide and debugger
#          - added allv.html, still only demos (games later), added getKnownDemos()
#          - fixed binary download (wb)
#          - added dms support (one disk only, yet)
#          - working on installing the first demo (Not Again) - worked fully automated at 8:53 pm
#          - needs cleanup, make work for other dms prods, control install dirs and other heuristics, keep track of changes?

import os,sys
from lxo_helpers import dicthelpers

print "Wim.py v0.03, WHDLoad Install Manager by Leif Oppermann (13.10.2013)"
print "automates your WHDLoad installation chores"

# handle 3 key differences between Win32 2.7 and Amiga Python 2.0
config = {}
try:
    if True:
        config["has_boolean"]=True
except:
    True= 1
    False = 0
    config["has_boolean"]=False

try:
    from bs4 import BeautifulSoup
    config["has_bs4"]=True

except:
    config["has_bs4"]=False

try:
    import urllib
    config["has_urllib"]=True
except:
    config["has_urllib"]=False
    
def q(cond, on_true, on_false):
    return {True: on_true, False: on_false}[cond is True]

print "Capacilities are: 'urllib'-%s, 'bs4'-%s" % (q(config["has_urllib"],"True","False"), q(config["has_bs4"],"True","False"))

class whdloadWebProxyDemos:

    url_all= "http://www.whdload.de/demos/all.html"
    url_allv = "http://www.whdload.de/demos/allv.html"
    url_path = "http://www.whdload.de/demos/"

    cachedir = "cache"
    amidisk = "ff0:"
    tempdir = "t:"
    isAmiga = -1
    
    lastt = None
    
    prods = {}  # results will go here
    dh=None
    
    def __init__(self):
        self.dh=dicthelpers()
        if self.checkConfig():
            # cant currently build on Amiga Python 2.0
            self.buildTables(recursive=False)
            self.saveDict()
        else:
            self.loadDict()

    def checkConfig(self):
        '''
        Checks if platform can run buildtables with Bs4 (eg win32), or not (amiga)
        Returns True if it can, otherwise False
        '''
        vi = sys.version_info
        major = vi[0]
        minor = vi[1]
        micro = vi[2]
        platform = sys.platform.capitalize()

        print "Running Python v%d.%d.%d on %s - %s" % (major,minor,micro,platform,sys.version)
        
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
                
        if okversion:
            print "--> generator functionality (scrape website, build tables)"
            self.isAmiga=False
        else:
            print "--> installer functionality (install)"
            self.isAmiga=True
        return okversion
        
    def saveDict(self):
        self.dh.saveDictionary(repr(self.prods),"brain.dict")
        return
        
    def loadDict(self):
        self.prods=eval(self.dh.loadDictionary("brain.dict"))
        
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
    
    def parseIndexAll(self, recursive=False, debug=True):
        s = self.cacheGet(self.url_all)
        docname = os.path.basename(self.url_all)
        # parse html
        w = BeautifulSoup(s)
        
        string =  "Parsing index '%s' with title '%s' .. " % (docname,w.title.string)
        sys.stdout.write(string)
        
        # collect table rows
        tr= w.find_all("tr")
        print "found %d entries" % (len(tr))
        
            
        # iterate over all listed demos and get their product html as well
        count=1
        for t in tr:
            if str(t).startswith("<tr><th"):
                if debug:
                    print "not a demo: %s" % str(t)
            else:
                try:
                    # all links in that line
                    # first is install, second info, ... last is images
                    a = t.find_all("a")
                    install = a[0].get("href")
                    info = a[1].get("href")
                    
                    if debug:
                        print "%d: %s (%s)" %(count,install,info)
                    
                    # get cached copies
                    # info
                    #s= self.cacheGet(os.path.join(self.url_path,info))
                    # install (needs redoing later)
                    s= self.cacheGet(os.path.join(self.url_path,install))
                    
                    # for easier reuse in pyshell
                    self.lastt = t
                    
                    # get product name as of whdload page(not validated for amiga compatibility as a filename, might have / and & and () in it)
                    prodname = a[0].getText()
                    if debug:
                        print "  "+ prodname

                    # try to be clever about required images (which are not uniformly declared on the website)
                    images = self.buildImagesMeta(prodname, a.pop().get("href"))
                    
                    # fill meta data structure
                    meta = {}
                    meta["prodname"]=prodname
                    meta["groupname"]="?"
                    meta["fromindex"]=docname
                    meta["info"]=info
                    meta["install"]=install
                    meta["images"]=images
                    meta["infoparsed"]=False
                    self.prods[prodname] = meta
                    
                except:
                    print "***error at %s" % str(t)
                    print "Unexpected error:", sys.exc_info()
                    raise
                count += 1  
    
    def buildImagesMeta(self, demo, hint):
        '''
        consume non deterministic pointer to images and try to be clever about it
        input: last entry from the line from the list of installs
        out dictionary with 
        '''
        if demo=="Not Again":
            print "--> parsing image locations"
            # one disks first, start with dms
            
            # get basename
            seenat, filename = os.path.split(hint)
            
            # get suffix
            trash, ext = os.path.splitext(hint)
            ext=ext.lower()
            
            print demo, seenat, filename, ext
            
            # only dms for the moment
            if ext!= ".dms":
                return {}
            
            print "still here"
            
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
        
        
    def parseIndexAllV(self, recursive=False, debug=True):
        s = self.cacheGet(self.url_allv)
        docname = os.path.basename(self.url_allv)
        # parse html
        w = BeautifulSoup(s)
        
        string =  "Parsing index '%s' with title '%s' .. " % (docname,w.title.string)
        sys.stdout.write(string)
        
        # collect table rows
        tr= w.find_all("tr")
        print "found %d entries" % (len(tr))
        
        
        
        # iterate over all listed demos and get their product html as well
        count=1
        for t in tr:
            if str(t).startswith("<tr><th"):
                if debug:
                    print "not a demo: %s" % str(t)
            else:
                try:
                    # all links in that line
                    # first is install, second info, ... last is images
                    a = t.find_all("a")
                    if len(a)>=2:
                        install = a[0].get("href")
                        info = a[1].get("href")
                        images = a.pop().get("href")
                        if debug:
                            print "%d: %s (%s)" %(count,install,info)
                        
                        # get cached copies
                        # info
                        #s= demos.cacheGet(os.path.join(demos.url_path,info))
                        # install (needs redoing later)
                        #s= demos.cacheGet(os.path.join(demos.url_path,install))
                        
                        # for easier reuse in pyshell
                        self.lastt = t
                        
                        # get product name as of whdload page(not validated for amiga compatibility as a filename, might have / and & and () in it)
                        groupandprodname = a[0].getText()
                        seperator=" - "
                        minusat = groupandprodname.find(seperator)
                        groupname = groupandprodname[:minusat]
                        prodname = groupandprodname[minusat+len(seperator):]
                        
                        if debug:
                            print "     %s: %s" % (groupname, prodname)
                        
                        # fill meta data structure
                        meta = {}
                        meta["prodname"]=prodname
                        meta["groupname"]=groupname
                        meta["fromindex"]=docname
                        meta["info"]=info
                        meta["install"]=install
                        meta["infoparsed"]=False                        
                        self.prods[prodname] = meta
                        
                        # debug
                        #if prodname=="Face Another Day":
                        #    print "bork at count: %d" % count
                        
                        # slow, can be done on request
                        if recursive:
                            self.parseInfo(prodname,debug=False)
                    
                except:
                    print "***error at %s" % str(t)
                count += 1  
  
    def parseInfo(self, demoname, debug= True):
        '''
        Parses info page of prod demoname upon request
        '''
        if config["has_bs4"]==False:
            return
        s = self.cacheGet(self.url_path + self.prods[demoname]["info"])
        # parse html

        if debug:
            string =  "Parsing info for '%s' .. " % (demoname)
            sys.stdout.write(string)
        else:
            sys.stdout.write(".")
                
        w = BeautifulSoup(s)
        
        if debug:
            print w
        
            print "*** End info"
        
        # collect table rows
        #tr= w.find_all("tr")
        #print "found %d entries" % (len(tr))
        
        # mark as done
        self.prods[demoname]["infoparsed"]=True
        return
    
    def hasDemo(self, demoname):
        '''
        Return True if demoname is known
        '''
        return self.prods.has_key(demoname)
    
    def getMeta(self, demoname, debug=False):
        if self.hasDemo(demoname):
            if self.prods[demoname]["infoparsed"]==False:
                # get details
                self.parseInfo(demoname, debug)
            return self.prods[demoname]
        else:
            return None
    
    def getKnownDemos(self):
        for prod in self.prods.keys():
            print "%s by %s" % (self.prods[prod]["prodname"], self.prods[prod]["groupname"])
        

    def buildTables(self, recursive=False, debug=False):
        '''
        Cache relevant content and parse demo list
        '''
        self.parseIndexAll(recursive, debug=False)
        self.parseIndexAllV(recursive, debug=False)
        
    def install(self, demoname, debug=False):
        '''
        install a demo, getting all required linked images, etc
        currently works with .dms 1 disk 1 image only
        returns True on success and False otherwise
        '''      
        data = self.prods[demoname]
        print "---> Installing %s by %s" % (demoname, data["groupname"])

        commands=[] # these will be executed one after another on target system

        # make sure to have metadata
        meta = self.getMeta(demoname)
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
            dmsline = "xdms u %s" % (fname)
            adfname = image["file"].replace(image["type"],".adf")
            if debug:
                print "Creating %s from %s" %(adfname, fname)

            #os.system(dmsline)
            commands.append(dmsline)
            print adfname
            
                      
        # unpack installer
        iname = os.path.join(self.cachedir, data["install"])
        lhaline = "lha x -N %s %s" % (iname ,self.tempdir)
        # "lha e -x0 -N %s #?.inf #?.slave #?README %s"%(iname ,self.tempdir)
        commands.append(lhaline)

        # ab hier wirds h?sslich hardcoded zum ende des tages :)
        # hardcoded for Sanity
        #commands.append('cd "t:NotAgain Install"')
        
        # DIC produces Disk.1
        copyline = 'copy %s to "t:NotAgain Install/Disk.1"' %(adfname)
        commands.append(copyline)
        #commands.append('list "t:NotAgain Install/"')
        
        #commands.append('cd "t:NotAgain Install/"')
        commands.append('rename "t:NotAgain Install/NotAgain.inf" "t:NotAgain Install/NotAgain.info"')
        commands.append('list "t:NotAgain Install/"')
        commands.append('cd "t:NotAgain Install/"\nwhdload Notagain.slave')
        # recap
        print "\n\n--> List of commands:"
        for command in commands:
            print command
        
        # go (amiga only)
        if not self.isAmiga:
           print "*** Error: Not running on Amiga!"
           return

        for command in commands:
            os.system(command)
            
        
        return

def test(demo):
    has = demos.hasDemo(demo)
    print "%s, %s" % (demo, has)
    if has:
        print "  %s" % demos.getMeta(demo, debug= False)
        # try to install
        demos.install(demo, debug=True)
        
        

# instantiate
demos = whdloadWebProxyDemos()

# test amiga and pc
#print demos.prods

#print demos.getKnownDemos()

test("Not Again")
#test("Planet M")
#test("Dizzy Tunes")
#test("Dizzy Tunes 2")
#test("Face Another Day")
#test("Voyage")




