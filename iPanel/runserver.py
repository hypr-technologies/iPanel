# coding: utf-8
# +-------------------------------------------------------------------
# | iPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2025 Hypr Technologies
# | Licensed under the MIT License
# | https://github.com/hyprtech/ipanel/blob/main/LICENSE
# +-------------------------------------------------------------------
# | Based on original work by iPanel (2015-2099)
# | Original Author: hwliang <hwl@hypr.local>
# +-------------------------------------------------------------------
from os import environ
from BTPanel import app,sys

if __name__ == '__main__':
    f = open('data/port.pl')
    PORT = int(f.read())
    HOST = '0.0.0.0'
    f.close()
    app.run(host=HOST,port=PORT)
