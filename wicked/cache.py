#!/usr/bin/env python
import os.path
import sys
import shutil

try:
    import urllib
    from urlparse import urlparse
except:
    pass

class cache:
    cachedir=""
    def __init__(self, cachedir="data/cache"):
        self.cachedir=cachedir
        pass

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
        if percents <=100:
            sys.stdout.write('%s [%s] %d%s %s\r' % (prefix, bar, percents, '%', suffix)),
            sys.stdout.flush()
        if iteration == total:
            print("\r")

    def report(self, blockcount, blocksize, totalsize):
        # The hook will be passed three arguments; a count of blocks transferred so far, a block size in bytes,
        # and the total size of the file.
        # https://docs.python.org/2/library/urllib.html
        # print blockcount, blocksize, totalsize
        if False:   #totalsize>-1:    # -1 on old FTP servers
            # known totalsize
            #sys.stdout.write('%d bytes\r' % (blockcount*blocksize) )
            #sys.stdout.flush()
            prefix = "  %d bytes" % totalsize
            self.printProgress(blockcount, int(totalsize/blocksize), prefix, suffix="Complete", decimals=2, barLength=60)
        else:
            # unknown totalsize
            sys.stdout.write('  %d bytes\r' % (blockcount*blocksize) )
            sys.stdout.flush()

    def getpathname(self, url):
        '''
        Return pathname of cached content or None

        Returns a string or None
        '''

        #basename = os.path.basename(url)
        #filename = os.path.join(self.cachedir, basename)
        o = urlparse(url)
        netloc = o.netloc
        netpath = o.path
        fullname = netloc+netpath
        return fullname

    def getfilename(self, url, debug=False):
        '''
        Return full filename of cached content or None

        Returns a string or None
        '''

        fullname = self.getpathname(url)
        filename = os.path.join(self.cachedir, fullname)
        if debug:
            print filename
        if os.path.exists(filename):
            return filename
        else:
            return None

    def get(self, url, debug=False, flat=True):
        '''
        Gets content from a URL and drops a copy in cachedir. Will use content from the cached file from then on.
        
        Limitations:
        - Currently does not handle multiple basenames from different URLs
        - Cache does not expire
        
        Returns a string
        '''

        if flat:
            # flat cache dir is handy for www.whdload.de files
            head, tail = os.path.split(url)
            fullname = tail
        else:
            # otherwise use full path hierarchy
            fullname = self.getpathname(url)
        filename = os.path.join(self.cachedir, fullname)
        if debug:
            print filename
        
        # strategy 1: try getting a cached copy and return
        if debug:
            print "***%s"%filename
        if os.path.exists(filename):
            if debug:
                print "***exists"
            # open the existing file
            file=open(filename)
            if file:
                content = file.read()
                file.close()
                return content
            
        # strategy 2: try getting the url, drop a cached binary copy, and return the content
        # 30.11.14: does not actually work well on Amiga. Gets stuck after 4/8 kb, e.g. with sanity-arte.dms (tests with adl.py)
        try:
            #print "***urllib.retrieve"
            # 2: create required dirs
            head, tail = os.path.split(filename)
            if not os.path.exists(head):
                if debug:
                    print "cache: need to create directory %s" % head
                shutil.os.makedirs(head)
            (localfilename, headers)=urllib.urlretrieve(url, filename, self.report)
            #content = urllib.urlopen(url).read()
            #savefile = open(filename, "wb")
            #savefile.write(content)
            #savefile.close()
            # open the existing file
            file=open(localfilename)
            if file:
                content = file.read()
                file.close()
                return content
        except:
            content=""
                
        return content    

if __name__ == '__main__':
    u = "http://aminet.net/pub/aminet/demo/track/Rampage.lha"
    o = cache(cachedir="t:\\")
    r = o.get(u, debug=True)
    print len(r)

    q = o.getfilename(u)
    print q
