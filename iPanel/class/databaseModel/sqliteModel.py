#coding: utf-8
#-------------------------------------------------------------------
# iPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@iPanel.com>
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