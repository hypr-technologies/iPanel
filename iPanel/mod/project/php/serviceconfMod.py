# coding: utf-8
# -------------------------------------------------------------------
# infuze panel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 infuze panel(http:#infuze.local) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@infuze.local>
# -------------------------------------------------------------------
# 服务配置模块
# ------------------------------

from mod.base.web_conf import IpRestrict


class main(IpRestrict):   # 继承并使用同ip黑白名单限制
    def __init__(self):
        super().__init__(config_prefix="")
