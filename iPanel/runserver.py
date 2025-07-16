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
import os
import sys
sys.path.insert(0, os.path.abspath('class'))
from BTPanel import app

if __name__ == "__main__":
    with open("data/port.pl") as f:
        PORT = int(f.read())
    HOST = "0.0.0.0"
    app.run(host=HOST, port=PORT)


