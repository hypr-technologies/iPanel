#coding: utf-8
#-------------------------------------------------------------------
# iPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@iPanel.com>
#-------------------------------------------------------------------

# 备份
#------------------------------
import os,sys,re,json,shutil,psutil,time
from panelModel.base import panelBase
import public

class main(panelBase):


    def __init__(self):
        pass


    def get_site_backup_info(self,get):
        """
        @获取网站是否开启计划任务备份
        @param get['site_id'] 网站id
        @return
            all : 开启全部网站备份
            info：计划任务详情
        """

        id = get.id
        find = public.M('sites').where("id=?",(id,)).find()
        if not find:
            return public.returnMsg(False, public.lang('The specified website could not be found.'))

        result = {}
        result['all'] = 0
        result['info'] = False
        result['status'] = True
        data =  public.M('crontab').where('sName=? and sType =?',(find['name'],'site')).order('id desc').select()
        if len(data) > 0:
            result['info'] = data[0]

        data =  public.M('crontab').where('sName=? and sType =?',('ALL','site')).order('id desc').select()
        if len(data) > 0:
            result['info'] = data[0]
            result['all'] = 1
        return result


    def get_database_backup_info(self,get):
        """
        @获取数据库是否开启计划任务备份
        @param get['site_id'] 数据库id
        @return
            all : 开启全部数据库备份
            info：计划任务详情
        """

        id = get.id
        find = public.M('databases').where("id=?",(id,)).find()
        if not find:
            return public.returnMsg(False, public.lang('The specified database could not be found.'))

        result = {}
        result['all'] = 0
        result['info'] = False
        result['status'] = True
        data =  public.M('crontab').where('sName=? and sType =?',(find['name'],'database')).order('id desc').select()
        if len(data) > 0:
            result['info'] = data[0]

        data =  public.M('crontab').where('sName=? and sType =?',('ALL','database')).order('id desc').select()
        if len(data) > 0:
            result['info'] = data[0]
            result['all'] = 1
        return result







