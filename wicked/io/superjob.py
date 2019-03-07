#!/usr/bin/env python
# 03.06.2016, noname

# superjob is the super class for all io jobs

class superjob:
    def __init__(self, name="superjob", debug=True):
        self.debug=debug
        self.name=name
        #if self.debug:
        #    print "super of %s init" % self.name
    
    def __exit__(self):
        pass
        #if self.debug:
        #    print "%s exit" % self.name
        
    def execute(self):
        if self.debug:
            print "%s execute" % self.name
        
    def test(self, echo="just a super convenience function"):
        print echo
    
        
    
#class childa(superjob):
#    def __init__(self):
#        self.name="childa"
#        print "%s init" % self.name
 
# childs to do as follows:
class childa(superjob):
    def __init__(self, name="childa", debug=True):
        superjob.__init__(self, name=name, debug=debug)
        if self.debug:
            print "%s init ctd." % self.name

if __name__ == '__main__':
    o=childa("example", True)   # set to False to suppress debug output
    o.execute()
    o.test()
    o.__exit__()