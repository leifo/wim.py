# common helpers
# lxo 2006-2008, 2016

class dicthelpers:
    # returns dictionary from given file
    # return empty dict {} if file not found
    def loadDictionary(self,filename):
        dict = {}
        try:
            file=open(filename,"rb")
            s = file.read()
            dict=eval(s)
            file.close()
        except:
            pass
        return dict

    # save given dictionary to given filename
    # fails silently in case of error
    def saveDictionary(self, dict, filename):
        try:
            file=open(filename,"wb")
            file.write(repr(dict))
            file.close()
        except:
            pass
    # just count for stats
    # note: initially written for xmill
    def countToDict(self,dict,key):
        '''
        Increment dict[key] or create dict[key], resulting in a counter of occurences
        '''
        if dict.has_key(key):
            dict[key]+=1
        else:
            dict[key]=1

    # just count for stats
    # note: initially written for xmill
    def logValueToDict(self,dict,key,value):
        '''
        Append value to list at dict[key] or create list at dict[key], resulting in a list of occurences
        '''
        if dict.has_key(key):
            dict[key].append(value)
        else:
            dict[key]=[value]
            
    def invertDict(self,dict):
        '''
        new, untested, taken from parseapset.py (in a different context)
        '''
        invert={}
        for k in dict:
            v = dict[k]
            if not invert.has_key(v):
                #print "generate key"
                invert[v]=[]
            invert[v].append(k)
        return invert
    def invertDict2(self,dict):
        '''
        only works on symmetrical data! (new, untested, no sanity checks)
        '''
        invert={}
        for k in dict:
            v = dict[k]
            invert[v]=k
        return invert

class listhelpers:
    '''
    # list tricks from http://bytes.com/forum/thread19083.html
    intersection = filter(lambda x: x in l1, l2)
    union = l1 + filter(lambda x: x not in l1, l2)
    difference = filter(lambda x: x not in l2, l1)
    '''
    def __init__(self):
        pass
    def intersection(self,l1,l2):
        return filter(lambda x: x in l1, l2)
    def union(self,l1,l2):
        return l1 + filter(lambda x: x not in l1, l2)
    def difference(self,l1,l2):
        #filter(lambda x:x not in l2,l1)
        filter(lambda x:x not in l2,l1)
'''
lh = listhelpers()
l1 = [1,2,3,4]
l2 = [2,3,4]
l3 = [3,4]
l4 = [4]
l5 = [5]
print lh.intersection(l1,l2)
print lh.intersection(l1,l3)
print lh.intersection(l1,l4)
print lh.intersection(l1,l5)
'''

class normalizer:
    '''
    normalize coordinates of given min and max into 0..1 range
    init with test = normalizer(100,200)
    print test.norm(150)
    should return 0.5
    lxo, october 2007
    '''
    min=max=range=0
    def __init__(self,min, max):
        if max<min:
            temp = max
            max = min
            min = temp
        self.min = min
        self.max = max
        self.range = max - min
        #print "got min: %f, max: %f (range: %f)" %(min,max,self.range)
    def norm(self,value):
        '''
        normalizes a value into 0..1
        results will be clamped, so never go beyond bounds of 0 and 1
        '''
        if value > self.max: return 1
        if value < self.min: return 0

        if self.range==0:
            return self.min
        else:
            return float(value - self.min)/self.range

# from http://stackoverflow.com/questions/2208828/detect-64bit-os-windows-in-python
def is_os_64bit():
    return platform.machine().endswith('64')

def getPlatformString():
    # try to build a platform string that can be used to call correspondingly named tools in \bin
    # returns: win32 (on any Windows), darwin-powerpc (on my PPC 10.4), amiga (on any Amiga)
    # linux2: i686 for centrino 32 bit laptop, x86_64 for desktop
    # todo: check darwin-intel string and name tools accordingly (i386)
    # sys.platform: amiga, darwin, win32
    # platform.processor: amiga (n.a.), darwin (powerpc), win32 (disregard as too much detail)
    import sys
    plat = sys.platform
    if  plat == "win32":
        return plat

    if  plat == "amiga":
        return plat

    import platform
    cpu = platform.processor()
    s = "%s-%s" %(plat, cpu)
    return s

