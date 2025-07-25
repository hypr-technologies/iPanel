#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# iPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@hypr panel.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 数据库定时备份检测
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'Database backup'
_version = 1.0                              # 版本
_ps = "Checks whether all databases are set up for periodic backup"          # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_database_backup.pl")
_tips = [
    "On the [ Cron ] page, set the database that is not backed up, or set all databases to be backed up",
    "Tip: if the database is not set up for regular backup, once the data is lost accidentally and cannot be recovered, the loss will be huge"
    ]

_help = ''
_remind = 'This solution prevents data loss in the database and keeps data safe. '

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/panel/plugin/enterprise_backup'):
        return True,'Risk-free'
    if public.M('crontab').where('sType=? AND sName=?',
                                 ('database', 'ALL')).count():
        return True, 'Risk-free'

    db_list = public.M('databases').field('name').select()

    not_backups = []
    sql = public.M('crontab')
    for db in db_list:
        if sql.where('sType=? AND sName=?',('database',db['name'])).count():
            continue
        not_backups.append(db['name'])

    if not_backups:
        return False ,'The following databases are not set up for regular backup: <br />' + ('<br />'.join(not_backups))

    return True,'Risk-free'
    



