# coding: utf-8
# -------------------------------------------------------------------
# iPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 iPanel(http:#hypr.local) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@hypr.local>
# -------------------------------------------------------------------
# 服务配置模块
# ------------------------------

from mod.base.web_conf import IpRestrict


class main(IpRestrict):   # 继承并使用同ip黑白名单限制
    def __init__(self):
        super().__init__(config_prefix="")


