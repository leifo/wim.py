#!/usr/bin/env python
# 10.10.13 - first test on WHDLoad Installer with BeautifulSoup HTML parsing
import urllib
import os
from bs4 import BeautifulSoup


class whdloadWebProxyDemos:
    url_all= "http://www.whdload.de/demos/all.html"
    url_allv = "http://www.whdload.de/demos/allv.html"
    url_path = "http://www.whdload.de/demos/"

    lastt = None
    
    prods = {}  # results will go here
    
    def __init__(self):
        self.buildTables()
        pass
    
    def cacheGet(self, url):
        '''
        Gets content from a URL and drops a copy in cachedir. Will use content from the cached file from then on.
        
        Limitations:
        - Currently does not handle multiple basenames from different URLs
        - Does break lha / binary
        
        Returns a string
        '''
        cachedir = "cache"
        
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
            
        # strategy 2: try getting the url, drop a cached copy, and return the content
        content = urllib.urlopen(url).read()
        savefile = open(filename, "w")
        savefile.write(content)
        savefile.close()
        return content
    
    def buildTables(self, debug=False):
        '''
        Cache relevant content and parse demo list
        '''
        s = self.cacheGet(self.url_all)        
        # parse html
        w = BeautifulSoup(s)
        
        print w.title.string
        
        # collect table rows
        tr= w.find_all("tr")
        print "Found %d rows in table" % len(tr)
        
        
        
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
                    prodname = a[0].getText()
                    if debug:
                        print "  "+ prodname
                    
                    # fill meta data structure
                    meta = {}
                    meta["prodname"]=prodname
                    self.prods[prodname] = meta
                    
                except:
                    print "***error at %s" % str(t)
                count += 1  
    
    def hasDemo(self, demoname):
        '''
        Return True if demoname is known
        '''
        return self.prods.has_key(demoname)
    
    def getMeta(self, demoname):
        if self.hasDemo(demoname):
            return self.prods[demoname]
        else:
            return None
    
# instantiate
demos = whdloadWebProxyDemos()
m = demos.getMeta("Planet M")
print m 


