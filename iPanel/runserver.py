#coding: utf-8
# +-------------------------------------------------------------------
# | iPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@hypr panel.com>
# +-------------------------------------------------------------------
from os import environ
from BTPanel import app,sys

if __name__ == '__main__':
    f = open('data/port.pl')
    PORT = int(f.read())
    HOST = '0.0.0.0'
    f.close()
    app.run(host=HOST,port=PORT)
