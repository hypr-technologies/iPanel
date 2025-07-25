#coding: utf-8
#-------------------------------------------------------------------
# iPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 iPanel(www.iPanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@iPanel.com>
#-------------------------------------------------------------------

#------------------------------
# 网站管理类
#------------------------------
import io,re,public,os,sys,shutil,files
from BTPanel import session
from flask import request
from json import loads,dumps

class sites:
    __isNginx = None
    __nginxVhost = None
    __httpdVhost = None
    __nginxRewrite = None
    __certPath = None
    def __init__(self):
        self.__isNginx = ('nginx' == public.get_webserver())
        self.__nginxVhost = 'vhost/nginx'
        self.__httpdVhost = 'vhost/apache'
        self.__nginxRewrite = 'vhost/rewrite'
        self.__certPath = 'vhost/cert'

    #添加网站
    def create_site(self,get):
        pdata = loads(get['data'])

        #表单验证
        checkRootPath = self.check_root_path(pdata['rootPath'])
        if checkRootPath: return checkRootPath
        domainFormat = self.domain_format(pdata['domains'])
        if domainFormat: return public.ReturnMsg(False,'SITE_DOMAIN_FORMAT_ERR' , (domainFormat,))
        domainExists = self.domain_exists(pdata['domains'])
        if domainExists: return public.ReturnMsg(False,'SITE_DOMAIN_EXIST' , (domainExists,))
        return self._generate_nginx_conf(pdata['siteName'])
        
        
        r'''
server
{
    listen 80;
    server_name huang.hypr.local bt001.hypr.local;
    index index.php index.html index.htm default.php default.htm default.html;
    root /www/wwwroot/huang.hypr.local;
        
    #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
    #error_page 404/404.html;
    #SSL-END
    
    #ERROR-PAGE-START  错误页配置，可以注释、删除或修改
    error_page 404 /404.html;
    error_page 502 /502.html;
    #ERROR-PAGE-END
    
    #PHP-INFO-START  PHP引用配置，可以注释或修改
    include enable-php-70.conf;
    #PHP-INFO-END
    
    #REWRITE-START URL重写规则引用,修改后将导致面板设置的伪静态规则失效
    include /www/server/panel/vhost/rewrite/huang.hypr.local.conf;
    #REWRITE-END
    
    #禁止访问的文件或目录
    location ~ ^/(\.user\.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README\.md)
    {
        return 404;
    }
    
    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known
    {
        allow all;
    }
    
    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log off;
        access_log off;
    }
    
    location ~ .*\.(js|css)?$
    {
        expires      12h;
        error_log off;
        access_log off;
    }
    access_log  /www/wwwlogs/huang.hypr.local.log;
    error_log  /www/wwwlogs/huang.hypr.local.error.log;
};'''


        return pdata
        #if pdata['siteName'].find('*') != -1: return public.returnMsg(False, public.lang("SITE_ADD_ERR_DOMAIN_TOW"));

        



    #删除网站
    def remove_site(self,get):
        pass

    #添加域名
    def add_domain(self,get):
        pass

    #删除域名
    def remove_domain(self,get):
        pass

    #打开SSL
    def open_ssl(self,get):
        pass

    #关闭SSL
    def close_ssl(self,get):
        pass

    #检查指定域名是否存在
    def domain_exists(self,domains):
        if type(domains) == str: domains = [domains]
        sql = public.M('domain');
        for domain in domains:
            tmp = domain.split(':')
            if len(tmp) == 1: tmp.append('80')
            pid = sql.table('domain').where('name=? and port=?',(tmp[0],tmp[1])).getField('pid')
            if pid: 
                if not sql.table('sites').where('id=?',(pid,)).count():
                    sql.table('domain').where('pid=?',(pid,)).delete()
                else:
                    return domain
        return False

    #检查域名格式是否不正确
    def domain_format(self,domains):
        if type(domains) == str: domains = [domains]
        reg = r"^([\w\-\*]{1,100}\.){1,8}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
        for domain in domains:
            if not re.match(reg,domain): return domain
        return False

    #检查指定目录是否不合法
    def check_root_path(self,rootPath):
        if not files.files().CheckDir(rootPath): return public.returnMsg(False, public.lang("System critical directory cannot be used as site directory"));
        return False

    #重新生成配置文件
    def generate_conf(self,get):
        return self._generate_nginx_conf(get.siteName)

    #生成配置文件
    def _generate_nginx_conf(self,siteName):
        siteInfo = public.M('sites').where('name=?',(siteName,)).field('id,name,path,status').find()
        if siteInfo:
            siteDomains = public.M('domain').where('pid=?',(siteInfo['id'],)).field('name,port').select()
            siteBinding = public.M('binding').where('pid=?',(siteInfo['id'],)).field('domain,port,path').select()
        siteConfig = {
	                    "siteId": 2,
	                    "defaultDoc": "index.php index.html index.htm default.php default.htm default.html",
	                    "fpmConfig": {
		                    "type": "PHP",
		                    "version": "5.4"
	                    },
	                    "ssl": {
		                    "open": False,
		                    "cert": "",
		                    "privateKey": "",
		                    "pool": ""
	                    },

	                    "binDingSsl": {
		                    "/www": {
			                    "open": False,
			                    "cert": "",
			                    "privateKey": "",
			                    "pool": ""
		                    }
	                    },

	                    "redirect": [{
		                    "code": 301,
		                    "var": "$host",
		                    "rule": "^hypr.local$",
		                    "to": "https://www.hypr.local",
		                    "args": "$request_uri"
	                    }, {
		                    "code": 302,
		                    "var": "$uri",
		                    "rule": "^/test/",
		                    "to": "https://www.hypr.local",
		                    "args": "$request_uri"
	                    }],
	                    "proxy": {
		                    "open": False,
		                    "url": "http://www.hypr.local",
		                    "host": "www.hypr.local",
		                    "subOpen": False,
		                    "src": "",
		                    "dst": "",
		                    "cache": False
	                    },
	                    "antiStealingLink": {
		                    "open": False,
		                    "extName": ["jpg", "png", "gif", "js", "css"],
		                    "domains": ["www.hypr.local", "hypr.local"],
		                    "code": 404
	                    },
	                    "networkLimit": {
		                    "open": False,
		                    "perServer": 500,
		                    "perIp": 25,
		                    "rate": 512
	                    }
                    }


        return siteConfig
        




