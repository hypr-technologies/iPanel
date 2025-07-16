#coding: utf-8
#-------------------------------------------------------------------
# Infuze Panel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 Infuze Panel(www.infuze panel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@infuze panel.com>
#-------------------------------------------------------------------

# 虚拟空间平台模型
#------------------------------
import os,re,json,time
# from virtualModelV2.base import virtualBase
from flask import request
import requests
import public
import yaml
from public.validate import Param
try:
    from BTPanel import session
except :pass

class main():
    setup_path = public.get_setup_path()
    default_yaml = '{}/vhost_virtual/manifest/config/default.yaml'.format(setup_path)
    ssl_yaml = '{}/vhost_virtual/config/template/ssl.yaml.tpl'.format(setup_path)
    not_ssl_yaml = '{}/vhost_virtual/config/template/not_ssl.yaml.tpl'.format(setup_path)
    cert_path = '{}/vhost_virtual/data/cert'.format(setup_path)
    crt_path = '{}/vhost.crt'.format(cert_path)
    key_path = '{}/vhost.key'.format(cert_path)
    not_auto_ssl_file= '{}/vhost_virtual/config/not_auto_ssl.pl'.format(setup_path)
    server_ip_file = '{}/vhost_virtual/config/server_ip.pl'.format(setup_path)
    server_domain_file = '{}/vhost_virtual/config/server_domain.pl'.format(setup_path)
    close_ssl_file= '{}/vhost_virtual/config/close_ssl.pl'.format(setup_path)
    not_accept_port_file = '{}/vhost_virtual/config/not_accept_port.pl'.format(setup_path)
    data={}
    firewall_exec="btpython /www/server/panel/script/vhost_virtual.py"
    VERSION_FILE = '{}/vhost_virtual/data/.ver'.format(public.get_setup_path())
    add_permissions='chmod +x {}/vhost_virtual/vhost_virtual'.format(public.get_setup_path())

    def __init__(self):
        pass

    def return_message_vhost(self,status,code, msg,error_msg,data):
        """
        @name 返回信息
        """
        return {"status":status,"code":code,"msg":msg,"error_msg":error_msg,"message":data}

    def forward_request(self,args,url):
        """
        @name 请求虚拟空间平台数据
        """
        if not self.get_service_status_achieve():
            return self.return_message_vhost(-1, 500,public.lang("Account service not started, please start the service first"),"",{})
        #携带"access_token"请求头
        access_token = public.ReadFile("/www/server/vhost_virtual/data/config/local_access_token.pl")
        
        if not access_token:
            access_token = ""
        vhost_port = ":8000"
        http_control = "http"
        with open(self.default_yaml, 'r') as file:
            self.data=yaml.safe_load(file)
            try:
                if self.data["server"].get("address"):
                    vhost_port=self.data["server"]["address"]
                if self.data["server"].get("httpsAddr"):
                    vhost_port = self.data["server"]["httpsAddr"]
                    http_control = "https"
            except Exception as e:
                public.print_log("e--------------:{}".format(e))
        # 请求 URL
        # url = http_control+'://'+ public.GetHost()+vhost_port+'/'+url
        host="127.0.0.1"
        host_file="/www/server/panel/data/domain.conf"
        if os.path.exists(host_file) and os.path.exists(self.server_domain_file):
            host=public.ReadFile(host_file)
            if not host or host.strip()=="":
                host="127.0.0.1"
            else:
                 host=host.strip()
        url = http_control+'://'+host+vhost_port+'/'+url
        # public.print_log("url:{}".format(url))
        # 发起请求
        response = requests.request(
            method="post",
            url=url,
            headers={'access_token': access_token},
            json=args.get_items(),
            verify=False,
        )
        if response.status_code == 200:
            return  response.json()
        else:
            return self.return_message_vhost(-1, 500,public.lang("Request failed"),"",{})

    def account(self,args):
        """
        @name 获取用户信息
        """
        return self.forward_request(args, 'account/get_account_list')



    def get_account_list(self,args):
        """
        @获取用户列表
        """
        if not self.get_service_status_achieve():
            return self.return_message_vhost(-1, 500,public.lang("Account service not started, please start the service first"),"",{})
        result = self.forward_request(args, 'account/get_account_list')
        if result.get("status") == -1:
            return self.return_message_vhost(0, 200, "获取成功","",result.get("message"))
        return result

    def remove_account(self,args):
        """
        @删除用户
        """
        return self.forward_request(args, 'account/remove_account')

    def modify_account(self,args):
        """
        @修改用户
        """
        return self.forward_request(args, 'account/modify_account')

    def create_account(self,args):
        """
        @创建用户
        """
        return self.forward_request(args, 'account/create_account')


    def get_type_list(self,args):
        """
        @获取分类列表
        """
        result = self.forward_request(args, 'account/get_type_list')
        if result.get("status") == -1:
            return self.return_message_vhost(0, 200, "获取成功","",result.get("message"))
        return result

    def create_type(self,args):
        """
        @创建分类
        """
        return self.forward_request(args, 'account/create_type')

    def remove_type(self,args):
        """
        @删除分类
        """
        return self.forward_request(args, 'account/remove_type')

    def modify_type(self,args):
        """
        @修改分类
        """
        return self.forward_request(args, 'account/modify_type')

    def package(self,args):
        """
        @name 获取资源包信息
        """
        return self.forward_request(args, 'account/get_package_list')


    def get_package_list(self,args):
        """
        @获取资源包列表
        """
        if not self.get_service_status_achieve():
            return self.return_message_vhost(-1, 500,public.lang("Account service not started, please start the service first"),"",{})
        return self.forward_request(args, 'account/get_package_list')

    def create_package(self,args):
        """
        @创建资源包
        """
        return self.forward_request(args, 'account/create_package')

    def modify_package(self,args):
        """
        @修改资源包
        """
        return self.forward_request(args, 'account/modify_package')

    def remove_package(self,args):
        """
        @删除资源包
        """
        return self.forward_request(args, 'account/remove_package')

    def logs(self,args):
        """
        @name 获取日志信息
        """
        return self.forward_request(args, 'log/get_logs')
    
    def get_logs(self,args):
        """
        @获取日志
        @sql_type = sqlserver
        """
        if not self.get_service_status_achieve():
            return self.return_message_vhost(-1, 500,public.lang("Account service not started, please start the service first"),"",{})
        return self.forward_request(args, 'log/get_logs')


    def clean_logs(self,args):
        """
        @清空日志
        @sql_type = sqlserver
        """
        return self.forward_request(args, 'log/clean_logs')
    
    def get_disk_list(self,args):
        """
        @获取磁盘列表
        """
        if not self.get_service_status_achieve():
            return self.return_message_vhost(-1, 500,public.lang("Account service not started, please start the service first"),"",{})
        return self.forward_request(args, 'account/get_disk_list')

    def set_default_disk(self,args):
        """
        @设置默认磁盘
        """
        return self.forward_request(args, 'account/set_default_disk')
        
    def get_account_temp_login_token(self,args):
        """
        @获取临时登录Token
        """
        return self.forward_request(args, 'account/get_account_temp_login_token')
        
    

    def one_key_login(self,args):
        """
        @一键登录
        """
        return self.forward_request(args, 'account/one_key_login')


    def check_virtual_service(self,args):
        """
        @检查虚拟空间服务是否安装
        """
        return self.forward_request(args, 'account/check_virtual')

    #开启指定挂载点的磁盘配额
    def enable_disk_quota(self,args):
        """
        @开启指定挂载点的磁盘配额
        """
        return self.forward_request(args, 'account/enable_disk_quota')


    def get_service_status_achieve(self):
        """
        @获取虚拟空间服务状态
        """
        result = public.ExecShell('systemctl status vhost_virtual.service')[0]
        if "Active: active (running)" in result:
            return True
        else:
            return False

    #启动虚拟空间服务
    def start_service(self,args):
        """
        @启动虚拟空间服务
        """
        public.ExecShell(self.add_permissions)
        public.WriteFile(self.not_accept_port_file,"true")
        public.ExecShell('systemctl start vhost_virtual.service')
        public.ExecShell('/www/server/v-apache/bin/apachectl graceful')
        os.remove(self.not_accept_port_file)
        # os.system("/etc/init.d/bt restart")
        if self.get_service_status_achieve():
            return public.return_message(0, 0, public.lang('start Successfully'))
        else:
            return public.return_message(-1, 0, public.lang('start Failed'))

    #停止虚拟空间服务
    def stop_service(self,args):
        """
        @停止虚拟空间服务
        """
        public.ExecShell(self.add_permissions)
        public.WriteFile(self.not_accept_port_file,"true")
        public.ExecShell('systemctl stop vhost_virtual.service')
        os.remove(self.not_accept_port_file)
        # os.system("/etc/init.d/bt restart")
        if self.get_service_status_achieve():
            return public.return_message(-1, 0, public.lang('stop Failed'))
        else:
            return public.return_message(0, 0, public.lang('stop Successfully'))

    #重启虚拟空间服务
    def restart_service(self,args):
        """
        @重启虚拟空间服务
        """
        public.ExecShell(self.add_permissions)
        public.WriteFile(self.not_accept_port_file,"true")
        public.ExecShell('systemctl restart vhost_virtual.service')
        public.ExecShell('/www/server/v-apache/bin/apachectl graceful')
        os.remove(self.not_accept_port_file)
        # os.system("/etc/init.d/bt restart")
        if self.get_service_status_achieve():
            return public.return_message(0, 0, public.lang('restart Successfully'))
        else:
            return public.return_message(-1, 0, public.lang('restart Failed'))

    #重载虚拟空间服务
    def reload_service(self,args):
        """
        @重载虚拟空间服务
        """
        public.ExecShell(self.add_permissions)
        #写入文件
        public.WriteFile(self.not_accept_port_file,"true")
        public.ExecShell('systemctl restart vhost_virtual.service')
        os.remove(self.not_accept_port_file)
        # os.system("/etc/init.d/bt restart")
        return public.return_message(0, 0, public.lang('reload Successfully'))

    #获取虚拟空间安装状态
    def get_service_info(self,args):
        """
        @获取虚拟空间安装状态 install_status 0 未安装 1 安装中 2 已安装  run_status 0 停止 1 运行中
        """
        install_status=0
        run_status=0
        if os.path.exists('{}/vhost_virtual'.format(self.setup_path)) and os.path.exists('{}/v-apache/bin/v-httpd'.format(self.setup_path)):
            install_status = 2
            # run_status = 1
            if self.get_service_status_achieve():
                run_status = 1
        elif public.M('tasks').where('name=? and status !=?',('Install [vhost_virtual-1.0]',1)).count() > 0:
            install_status = 1

        # 读取版本号
        ver = public.readFile(self.VERSION_FILE)

        # 无法直接从文件读取则设置默认值
        if not ver:
            ver = '1.0.0'

        return public.return_message(0, 0, {'install_status': install_status,"run_status":run_status, "version": ver})

    #获取虚拟空间安装进度
    def get_install_log(self,args):
        """
        @获取虚拟空间安装进度
        """
        log_string=public.ReadFile('/tmp/panelExec.log')
        return public.return_message(0, 0, log_string)

    #安装虚拟空间服务
    def install_service(self,args):
        """
        @安装虚拟空间服务
        """
        #检测证书目录是否存在，不存在则创建
        if not os.path.exists(self.cert_path):
            os.makedirs(self.cert_path)
        if public.get_webserver() !="nginx" or not os.path.exists('{}/nginx/sbin/nginx'.format(public.get_setup_path())):
            return public.return_message(-1, 0, public.lang('At present, only nginx is supported as the web server. Please adjust the web server to nginx first and backup the website data when adjusting the web server'))
        #
        download_url="https://www.infuze panel.com/script/Multi-user_install.sh"
        # download_url="http://192.168.66.161/install/Multi-user_install_____III.sh" #内网测试
        install_path="{}/panel/install".format(public.get_setup_path())
        install_file=install_path+"/vhost_virtual.sh"
        if os.path.exists(install_file):
            os.remove(install_file)
        public.ExecShell("wget -O "+install_file+" "+download_url+" --no-check-certificate")
        if not os.path.exists(install_file):
            return public.return_message(-1, 0, public.lang('Installation script download failed'))
        if public.M('tasks').where('name=? and status=?',('Install [vhost_virtual-1.0]','0')).count() > 0:
            return public.return_message(-1, 0, public.lang('The task already exists'))
        else:
            execstr="cd /www/server/panel/install && /bin/bash vhost_virtual.sh"
            public.M('tasks').add('id,name,type,status,addtime,execstr',(None, 'Install [vhost_virtual-1.0]','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
            public.writeFile('/tmp/panelTask.pl','True')
            # 提交安装统计
            import threading
            threading.Thread(target=requests.post, kwargs={
                'url': '{}/api/panel/panel_count_daily'.format(public.OfficialApiBase()),
                'data': {
                    'name': 'vhost_virtual',
                }}).start()
            # 添加放行端口
            import firewalls
            get = public.dict_obj()
            get.port = "50443"
            get.ps = "vhost virtual service"
            firewalls.firewalls().AddAcceptPort(get)
            return public.return_message(0, 0, public.lang('The installation task has been added to the task queue'))

    # 版本更新
    def update_service(self, args):
        # # 更新脚本（测试）
        # cmd = 'wget -O /www/server/vhost_virtual.zip http://192.168.66.99/vhost_virtual.zip && unzip -q -o /www/server/vhost_virtual.zip -d /www/server/ && systemctl restart vhost_virtual.service'
        # public.ExecShell(cmd)

        # 下载更新脚本
        download_url = "https://www.infuze panel.com/script/Multi-user_install.sh"
        install_path = "{}/panel/install".format(public.get_setup_path())
        install_file = install_path + "/vhost_virtual.sh"
        if os.path.exists(install_file):
            os.remove(install_file)
        public.ExecShell("wget -O " + install_file + " " + download_url + " --no-check-certificate")

        # 执行更新脚本
        cmd = 'cd /www/server/panel/install && /bin/bash vhost_virtual.sh'
        public.ExecShell(cmd)

        return public.return_message(0, 0, public.lang('The upgrade was successful'))


    #设置证书
    def save_server_ssl(self,args):
        args.certificate = args.certificate.strip()
        args.private_key = args.private_key.strip()
        #验证证书
        if not args.certificate or not args.private_key:
            return self.return_message_vhost(-1, 0, public.lang('Certificate content cannot be empty'),"",{})
        import ssl_info
        ssl_info = ssl_info.ssl_info()
        issuer = self.analyze_ssl(args.certificate)
        if issuer.get("organizationName") == "Let's Encrypt":
            args.certificate += "\n"
        if args.private_key.find('KEY') == -1:
            return self.return_message_vhost(-1, 0, public.lang('Private Key ERROR, please check!'),"",{})
        if args.certificate.find('CERTIFICATE') == -1:
            return self.return_message_vhost(-1, 0, public.lang('Certificate ERROR, please check!'),"",{})
        public.writeFile('/tmp/cert.pl', args.certificate)
        if not public.CheckCert('/tmp/cert.pl'):
            return self.return_message_vhost(-1, 0, public.lang('Error getting certificate'),"",{})

        # # 验证证书和密钥是否匹配格式是否为pem
        # check_flag, check_msg = ssl_info.verify_certificate_and_key_match(args.private_key, args.certificate)
        # if not check_flag: return self.return_message_vhost(-1, 0, public.lang(check_msg),"","")
        # 验证证书链是否完整
        check_chain_flag, check_chain_msg = ssl_info.verify_certificate_chain(args.certificate)
        if not check_chain_flag:
            return self.return_message_vhost(-1, 0, public.lang(check_chain_msg),"",{})
        backup_cert = '/tmp/backup_vhost_cert'
        backup_key = '/tmp/backup_vhost_key'

        # import shutil
        # if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        # if os.path.exists(backup_key): shutil.rmtree(backup_key)
        # if os.path.exists(crt_path): shutil.move(crt_path, backup_cert)
        # if os.path.exists(Key_path): shutil.move(Key_path, backup_key)
        old_cert = public.readFile(self.crt_path)
        old_key = public.readFile(self.key_path)
        if os.path.exists(self.crt_path): os.rename(self.crt_path,self.crt_path+".bak")

        #写入证书
        public.writeFile(self.crt_path,args.certificate)
        public.writeFile(self.key_path,args.private_key)
        public.ExecShell('chown www:www {} {}'.format(self.crt_path,self.key_path))
        ssl_config = public.readFile(self.ssl_yaml)
        public.writeFile(self.default_yaml,ssl_config)
        if os.path.exists(self.close_ssl_file): os.remove(self.close_ssl_file)
        public.ExecShell('systemctl restart vhost_virtual.service')
        if not self.get_service_status_achieve():
            if old_cert and old_key:
                public.writeFile(self.crt_path,old_cert)
                public.writeFile(self.key_path,old_key)
            else:
                if os.path.exists(self.crt_path):os.remove(self.crt_path)
                if os.path.exists(self.key_path):os.remove(self.key_path)
                not_ssl_config = public.readFile(self.not_ssl_yaml)
                public.writeFile(self.default_yaml,not_ssl_config)
            public.ExecShell('systemctl restart vhost_virtual.service')
            return self.return_message_vhost(-1, 0, public.lang('Please verify if the certificate format and content are correct'),"",{})

        public.writeFile(self.not_auto_ssl_file,'True')


        #放行端口
        public.M('tasks').add('id,name,type,status,addtime,execstr',(None, 'firewall accept port','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),self.firewall_exec))
        public.writeFile('/tmp/panelTask.pl','True')
        return self.return_message_vhost(0, 0, public.lang('set Successfully'),"",{})
        # return public.return_message(0, 0, public.lang('set Successfully'))

    def analyze_ssl(self, csr):
        issuer_dic = {}
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            cert = x509.load_pem_x509_certificate(csr.encode("utf-8"), default_backend())
            issuer = cert.issuer
            for i in issuer:
                issuer_dic[i.oid._name] = i.value
        except:
            pass
        return issuer_dic


    #关闭证书
    def close_server_ssl(self,args):
        public.WriteFile(self.close_ssl_file,"true")
        #删除备份
        if os.path.exists(self.crt_path+".bak"): os.remove(self.crt_path+".bak")
        if os.path.exists(self.key_path+".bak"): os.remove(self.key_path+".bak")
        if os.path.exists(self.crt_path): os.rename(self.crt_path,self.crt_path+".bak")
        if os.path.exists(self.key_path): os.rename(self.key_path,self.key_path+".bak")
        not_ssl_config = public.readFile(self.not_ssl_yaml)
        public.writeFile(self.default_yaml,not_ssl_config)
        public.ExecShell('systemctl restart vhost_virtual.service')
        #放行端口
        public.M('tasks').add('id,name,type,status,addtime,execstr',(None, 'firewall accept port','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),self.firewall_exec))
        public.writeFile('/tmp/panelTask.pl','True')
        public.writeFile(self.not_auto_ssl_file,'True')
        return self.return_message_vhost(0, 0, public.lang('close Successfully'),"",{})

    #获取证书
    def get_server_ssl(self,args):
        sslCert = public.readFile(self.crt_path)
        sslKey = public.readFile(self.key_path)
        if not sslCert or not sslKey:
            if os.path.exists(self.crt_path+".bak") and os.path.exists(self.key_path+".bak"):
                sslCert = public.readFile(self.crt_path+".bak")
                sslKey = public.readFile(self.key_path+".bak")
            else:
                sslCert = ''
                sslKey = ''
        return public.return_message(0, 0, {'certificate':sslCert,'private_key':sslKey})


    #设置ip地址
    def set_server_address(self,args):
        """
        @设置ip地址 ip ip地址 domain 域名
        """
        #验证ip地址
        if public.is_ipv6(args.address):
            return public.return_message(-1, 0, public.lang('IPv6 address is not supported'))
        if not public.checkIp(args.address) and not public.is_domain(args.address):
            return public.return_message(-1, 0, public.lang('Please check if the host address is correct, for example: 192.168.1.20'))
        if public.checkIp(args.address):
            public.WriteFile(self.server_ip_file,args.address)
            if os.path.exists(self.server_domain_file):
                os.remove(self.server_domain_file)
        else:
            public.WriteFile(self.server_domain_file,args.address)
            public.ExecShell('systemctl restart vhost_virtual.service')
            public.ExecShell("/etc/init.d/bt restart")
        return self.return_message_vhost(0, 0, public.lang('set Successfully'),"",{})

    #获取ip地址
    def get_server_address(self,args):
        """
        @获取ip地址
        """
        ip = ""
        domain = ""
        if os.path.exists(self.server_domain_file):
            domain = public.ReadFile(self.server_domain_file)
        try:
            ip = public.ReadFile(self.server_ip_file)
            if not ip: ip = public.GetClientIp()
        except:
            ip = public.GetClientIp()

        protocol = "http"
        port = ":8000"
        with open(self.default_yaml, 'r') as file:
            self.data=yaml.safe_load(file)
            try:
                if self.data["server"].get("httpsAddr"):
                    protocol = "https"
                    port = self.data["server"]["httpsAddr"]
                else:
                    if self.data["server"].get("address"):
                        port = self.data["server"]["address"]
            except Exception as e:
                pass
        
        
        return self.return_message_vhost(0, 200, "获取成功","",{"ip":ip,"domain":domain,"protocol":protocol,"port":port})





