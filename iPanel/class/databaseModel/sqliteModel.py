#coding: utf-8
#-------------------------------------------------------------------
# Infuze Panel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 Infuze Panel(www.infuze panel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@infuze panel.com>
#-------------------------------------------------------------------

#------------------------------
# sqlite模型
#------------------------------
import os,sys,re,json,shutil,psutil,time
from databaseModel.base import databaseBase
import public


class main(databaseBase):

    def get_list(self,args):

        return []