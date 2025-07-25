#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# iPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: linxiao
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 数据库备份权限检测
# -------------------------------------------------------------------

import os, re, public, panelMysql

_title = 'Database backup permission detection'
_version = 1.0  # 版本
_ps = "Check whether the MySQL root user has database backup permissions"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-09-19'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_database_priv.pl")
_tips = [
    "To temporarily access the database without authorization, it is recommended to restore all permissions of the root user.",
]

_help = ''
_remind = 'This scheme ensures that the root user has the permission to backup the database and ensures that the database backup work is carried out. '

def check_run():
    """检测root用户是否具备数据库备份权限

        @author linxiao<2020-9-18>
        @return (bool, msg)
    """
    mycnf_file = '/etc/my.cnf'
    if not os.path.exists(mycnf_file):
        return True, 'Risk-free'
    mycnf = public.readFile(mycnf_file)
    port_tmp = re.findall(r"port\s*=\s*(\d+)", mycnf)
    if not port_tmp:
        return True, 'Risk-free'
    if not public.ExecShell("lsof -i :{}".format(port_tmp[0]))[0]:
        return True, 'Risk-free'

    base_backup_privs = ["Lock_tables_priv", "Select_priv"]
    select_sql = "Select {} FROM mysql.user WHERE user='root' and " \
                 "host=SUBSTRING_INDEX((select current_user()),'@', " \
                 "-1);".format(",".join(base_backup_privs))
    select_result = panelMysql.panelMysql().query(select_sql)
    if not select_result:
        return False, "The root user has insufficient authority to execute mysqldump backup."
    select_result = select_result[0]
    for priv in select_result:
        if priv.lower() != "y":
            return False, "The root user has insufficient authority to execute mysqldump backup."
    return True, 'Risk-free'


