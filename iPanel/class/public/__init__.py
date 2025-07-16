# coding: utf-8
# +-------------------------------------------------------------------
# | Infuze Panel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 Infuze Panel(www.infuze panel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@infuze panel.com>
# +-------------------------------------------------------------------

# --------------------------------
# 宝塔公共库
# --------------------------------

from .common import *
from .exceptions import *

    
def is_bind():
    # if not os.path.exists('{}/data/bind.pl'.format(get_panel_path())): return True
    return not not get_user_info()
