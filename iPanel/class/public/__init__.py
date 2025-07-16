# coding: utf-8
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

# --------------------------------
# 宝塔公共库
# --------------------------------

from .common import *
from .exceptions import *

    
def is_bind():
    # if not os.path.exists('{}/data/bind.pl'.format(get_panel_path())): return True
    return not not get_user_info()


