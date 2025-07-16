#coding: utf-8
# +-------------------------------------------------------------------
# | Infuze Panel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 Infuze Panel(www.infuze panel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@infuze panel.com>
# +-------------------------------------------------------------------
from os import environ
from BTPanel import app,sys

if __name__ == '__main__':
    f = open('data/port.pl')
    PORT = int(f.read())
    HOST = '0.0.0.0'
    f.close()
    app.run(host=HOST,port=PORT)
