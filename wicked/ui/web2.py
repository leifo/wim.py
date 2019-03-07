#!/usr/bin/env python
# started working with bottly 21.08.14
# started working with bottle and bootstrap 28.08.14

import os

import bottle
from bottle import route, run, template, error, request, static_file, get, response

brain={}

#http://bottlepy.org/docs/dev/faq.html#template-not-found-in-mod-wsgi-mod-python
bottle.TEMPLATE_PATH.append("wicked\\ui\\views")

curdir = os.path.abspath(os.path.curdir)
viewdir=os.path.join(curdir, "wicked","ui","views")
staticdir=os.path.join(curdir, "wicked","ui","static")

bottle.TEMPLATE_PATH.append(viewdir)

print bottle.TEMPLATE_PATH

#--- web code
'''
@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')
'''

# Static Routes
# from http://stackoverflow.com/questions/10486224/bottle-static-files

@get('/<filename:re:.*\.js>')
def javascripts(filename):
    return static_file(filename, root=os.path.join(staticdir) )

@get('/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(filename, root=os.path.join(staticdir) )

@get('/<filename:re:.*\.(jpg|png|gif|ico)>')
def images(filename):
    return static_file(filename, root=os.path.join(staticdir) )

@get('/<filename:re:.*\.(eot|ttf|woff|svg)>')
def fonts(filename):
    return static_file(filename, root=os.path.join(staticdir) )






@error(404)
def error404(error):
    '''
    print "404:"
    print error
    print request
    print repr(response)
    '''
    return 'Nothing here, sorry'

@route('/hello/<name>')
def hello(name):
    #return template('<b>Hallo {{name}}</b>!', name=name)
    return template('hello', name=name)


       #'content', 'nocontent', 'prods', 'stats', 'noconnection'
        # sub dicts are as follows
        
        # content: - (lists what?)
        # nocontent: - (lists dead lines)
        # prods: - (lists all prods)
        # stats: category, iauthor, vendor
        # noconnection: -
        

@route('/content')
def content():
    return template("content", iter=brain["content"])

@route('/nocontent')
def nocontent():
    return template("nocontent", iter=brain["nocontent"])

@route('/prods')
def prods():
    #return template('<b>prods</b><br> Content: {{info}}', info=brain["prods"])
    #
    '''
    ''demos/Ramses_TheEngine': {'category': 'demos', 'info': 'Ramses_TheEngine.html', 'prodname': 'The Engine', 'vendor': 'Ramses', 'name': 'The Engine', 'oimages': 'amigascne:R/Ramses/TheEng
ine.lha', 'basename': 'Ramses_TheEngine', 'infoparsed': False, 'fromindex': 'refs.txt', 'id_hol': '', 'id_bitworld': '11
419', 'id_ada': '', 'install': 'Ramses_TheEngine.lha', 'id_lemon': '', 'images': {1: [{'seenat': 'http://ftp.amigascne.o
rg/pub/amiga/Groups/R/Ramses', 'type': '.lha', 'file': 'TheEngine.lha'}]}, 'iauthor': 'p', 'md5': [], 'id_pouet': '16464'},
    '''
    # print brain["prods"]['demos/Ramses_TheEngine']
    # print brain["prods"]['demos/Ramses_TheEngine']["info"]
    return template("prods", mydict=brain["prods"] )



@route('/stats')
def stats():
    return template("stats", iter=brain["stats"])

@route('/noconnection')
def noconnection():
    return template("noconnection", iter=brain["noconnection"])



@route('/')
def index():
    print "hit index"
    return template("index")


#--- control code
def runwebui():
    run(host='localhost', port=8080, debug=True, reloader=False)

def setBrain(content):
    global brain
    brain = content
    #print content
    
if __name__ == '__main__':
    runwebui()
