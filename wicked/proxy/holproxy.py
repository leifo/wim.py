#!/usr/bin/env python
# 12.06.2016

class holproxy:
    def __init__(self, debug=False):
        self.debug = debug
        self.baseurl="http://hol.abime.net/"
        self.middleurl="pic_full/dbs/"

    def __exit__(self):
        pass


    def getDbsUrl(self, id="1533"):
        '''
        generate url to hol dbs screenshot from given id

        matching this pattern
        http://hol.abime.net/pic_full/dbs/0001-0100/15_dbs1.png
        http://hol.abime.net/pic_full/dbs/0101-0200/153_dbs1.png
        http://hol.abime.net/pic_full/dbs/0201-0300/215_dbs1.png
        http://hol.abime.net/pic_full/dbs/0301-0400/315_dbs1.png
        ...
        http://hol.abime.net/pic_full/dbs/1501-1600/1533_dbs1.png
        '''

        url = self.baseurl + self.middleurl

        # build the folder name after middleurl, e.g. 0001-0100
        int_id = int(id)
        low = (int_id/100)*100 + 1
        high = low+99

        if int_id % 100 == 0:
            low = low-100
            high = high-100

        url = url+"%.4d-%.4d/%d_dbs1.png" % (low,high,int_id)
        print url



if __name__ == '__main__':
    o = holproxy(True)  # set to False to suppress debug output

    for h in range (0,6300,100):   # hol has screenshots for over 6100 titles!
        for i in range(3):
            o.getDbsUrl(h+i-1)
    o.__exit__()