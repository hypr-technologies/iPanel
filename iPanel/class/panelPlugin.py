#coding: utf-8
#-------------------------------------------------------------------
# iPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@hypr panel.com>
#-------------------------------------------------------------------
import public
import os
import sys
import json
import time
import psutil
import re
import shutil
import requests
from BTPanel import session, cache, send_file


if sys.version_info[0] == 3: from importlib import reload


class mget: pass


class panelPlugin:
    __list = 'data/list.json'
    __type = 'data/type.json'
    __index = 'config/index.json'
    __link = 'config/link.json'

    __official_url = public.OfficialApiBase()

    def __init__(self):
        self.__isTable = None
        self.__tasks = None
        self.__product_list = None
        self.__plugin_list = None
        self.__exists_names = {}
        self.__plugin_s_list = []
        self.__plugin_info = None
        self.__plugin_name = None
        self.__plugin_object = None
        self.__plugin_list = None
        self.__panel_path = '/www/server/panel'
        self.__plugin_path = self.__panel_path + '/plugin/'
        self.__plugin_save_file = self.__panel_path + '/data/plugin_bin.pl'
        self.__api_root_url = self.__official_url + '/api'
        self.__api_url = self.__api_root_url + '/panel/get_plugin_list'
        self.__download_url = self.__api_root_url + '/panel/download_plugin'
        self.__download_d_main_url = self.__api_root_url + '/panel/download_plugin_main'
        self._check_url = self.__api_root_url + '/panel/get_soft_list_status'
        self._unbinding_url = self.__api_root_url + '/panel/get_unbinding'
        self.__tmp_path = self.__panel_path + '/temp/'
        self.__plugin_timeout = 3600
        self.__is_php = False
        self.__install_opt = 'i'
        self.__pid = 0
        self.__path_error = self.__panel_path + '/data/error_pl.pl'
        self.__error_html = '/www/server/panel/BTPanel/templates/default/block_error.html'
        self.__sub_rules = []
        self.__replace_rule = []

        self.pids = None
        self.ROWS = 15

        self.__install_path = '/www/server/panel/plugin'

        if not self.__tasks:
            try:
                self.__tasks = public.M('tasks').where("status!=?", ('1',)).field('status,name').select()
            except:
                self.__tasks = []

        if not os.path.exists(self.__tmp_path):
            os.makedirs(self.__tmp_path, 0o755)

    # 检查依赖
    def check_deps(self,get):
        cacheKey = 'plugin_lib_list'
        if not 'force' in get:
            libList = cache.get(cacheKey)
            if libList: return libList
        libList = json.loads(public.readFile('config/lib.json'))
        centos = os.path.exists('/bin/yum')
        for key in libList.keys():
            for i in range(len(libList[key])):
                checks = libList[key][i]['check'].split(',')
                libList[key][i]['status'] = False
                for check in checks:
                    if os.path.exists(check):
                        libList[key][i]['status'] = True
                        break
                libList[key][i]['version'] = "-"
                if libList[key][i]['status']:
                    shellTmp = libList[key][i]['getv'].split(':D')
                    shellEx = shellTmp[0]
                    if len(shellTmp) > 1 and not centos: shellEx = shellTmp[1]
                    libList[key][i]['version'] = public.ExecShell(shellEx)[0].strip()
        cache.set(cacheKey,libList,86400)
        return libList

    #检测关键目录是否可以被写入文件
    def check_sys_write(self):
        test_file = '/etc/init.d/bt_10000100.pl'
        public.writeFile(test_file,'True')
        if os.path.exists(test_file):
            if public.readFile(test_file) == 'True':
                os.remove(test_file)
                return True
            os.remove(test_file)
        return False

    #检查互斥
    def check_mutex(self,mutex):
        if mutex == -1: return True
        mutexs = mutex.split(',')
        for name in mutexs:
            pluginInfo = self.get_soft_find(name)
            if not pluginInfo: continue
            if pluginInfo['setup'] == True:
                self.mutex_title = pluginInfo['title']
                return False
        return True

    #检查依赖
    def check_dependent(self,dependent):
        if not dependent: return True
        dependents = dependent.split(',')
        status = True
        for dep in dependents:
            if not dep: continue
            if dep.find('|') != -1:
                names = dep.split('|')
                for name in names:
                    pluginInfo = self.get_soft_find(name)
                    if not pluginInfo: return True
                    if pluginInfo['setup'] == True:
                        status = True
                        break
                    else:
                        status = False
            else:
                pluginInfo = self.get_soft_find(dep)
                if pluginInfo['setup'] != True:
                    status = False
                    break
        return status

    #检查CPU限制
    def check_cpu_limit(self,cpuLimit):
        if psutil.cpu_count() < cpuLimit: return False
        return True

    #检查内存限制
    def check_mem_limit(self,memLimit):
        if psutil.virtual_memory().total/1024/1024 < memLimit: return False
        return True

    #检查操作系统限制
    def check_os_limit(self,osLimit):
        if osLimit == 0: return True
        if osLimit == 1:
            centos = os.path.exists('/usr/bin/yum')
            return centos
        elif osLimit == 2:
            debian = os.path.exists('/usr/bin/apt-get')
            return debian
        return True

    # 检查安装限制
    def check_install_limit(self,get):
        if not hasattr(get,'pluginInfo'):
            pluginInfo = self.get_soft_find(get.sName)
        else:
            pluginInfo = get.pluginInfo
        p_node = '/www/server/panel/install/public.sh'
        if os.path.exists(p_node):
            if len(public.readFile(p_node)) < 100: os.remove(p_node)
        if not pluginInfo: return public.return_msg_gettext(False, public.lang("The specified plugin does not exist!"))
        self.mutex_title = pluginInfo['mutex']
        if not self.check_mutex(pluginInfo['mutex']): return public.return_msg_gettext(False, public.lang('Please uninstall [{}] first',self.mutex_title))
        if not hasattr(get, 'id'):
            if not self.check_dependent(pluginInfo['dependent']): return public.return_msg_gettext(False, public.lang('Depends on the following software, please install [{}] first',pluginInfo['dependent']))
        if 'version' in get:
            for versionInfo in pluginInfo['versions']:
                if versionInfo['m_version'] != get.version: continue
                if not 'type' in get: get.type = '0'
                if int(get.type) > 4: get.type = '0'
                if get.type == '0':
                    if not self.check_cpu_limit(versionInfo['cpu_limit']):
                        return public.return_msg_gettext(False, public.lang("At least [{0}] CPU cores are required to install", versionInfo['cpu_limit']))
                    if not self.check_mem_limit(versionInfo['mem_limit']):
                        return public.return_msg_gettext(False, public.lang("At least [{0} MB] memory is required to install", versionInfo['mem_limit']))
                if not self.check_os_limit(versionInfo['os_limit']):
                    m_ps = {0: "All", 1: "Centos", 2: "Ubuntu/Debian"}
                    return public.return_msg_gettext(False, public.lang('Only supports [{}] system',m_ps[int(versionInfo['os_limit'])]))
                if not hasattr(get, 'id'):
                    if not self.check_dependent(versionInfo['dependent']):
                        return public.return_msg_gettext(False,public.lang('Depend on the following software, please install first [{}]',versionInfo['dependent']))

    # 获取插件安装包下载进度
    def get_download_speed(self, get):
        '''
            @name 获取插件下载进度
            @author hwliang<2021-06-25>
            @param plugin_name<string> 插件名称
            @return dict
        '''
        result = self.__get_download_speed(get.plugin_name)
        return result

    # 取消下载
    def close_install(self, get):
        '''
            @name 取消指定插件安装过程
            @author hwliang<2021-07-07>
            @param plugin_name<string> 插件名称
            @return void
        '''
        plugin_name = get.plugin_name.strip()
        tmp_path = '{}/{}'.format(self.__tmp_path, plugin_name)
        if os.path.exists(tmp_path): shutil.rmtree(tmp_path)
        return public.returnMsg(False, public.lang("Installation process canceled!"))

    #安装插件
    def install_plugin(self,get):
        str1 = public.lang("System critical directory is not writable!")
        str2 = public.lang("1. If [System Hardening] is installed, please turn it off")
        str3 = public.lang("2. If Yunsuo is installed, please turn off [System Hardening] feature")
        str4 = public.lang("3. If Safedog is installed, please turn off [System Protection] feature")
        str5 = public.lang("4. If other security software is used, please uninstall it")
        if not self.check_sys_write():
            return public.return_msg_gettext(False,
                                             '<a style=color:red;>ERROR:{}</a><br>{}<br><br>{}<br>{}<br><br>'.format(
                                                 str1, str2, str3, str4))
        if not 'sName' in get: return public.return_msg_gettext(False, public.lang("Please specify the software name!"))
        #处理ols还不支持php81的情况
        # if get.sName == "php-8.1" and public.get_webserver() == 'openlitespeed':
        #     return public.return_msg_gettext(False, public.lang("Sorry, currently OLS official does not support php8.1"))
        pluginInfo = self.get_soft_find(get.sName)
        get.pluginInfo = pluginInfo
        check_result = self.check_install_limit(get)
        if check_result:
            return check_result
        if pluginInfo['name'] in ['dns_manager','mail_sys']:
            pluginInfo['type'] = 5

        if pluginInfo['type'] != 5:
            result = self.install_sync(pluginInfo,get)
        else:
            result = self.install_async(pluginInfo,get)
        try:
            if 'status' in result:
                if result['status']:
                    public.arequests('post','{}/setupPlugin'.format(self.__official_url),data={"pid":pluginInfo['id'],'p_name':pluginInfo['name']},timeout=3)
            # get.force = 1
            # self.get_cloud_list(get)
        except:pass
        return result

    #同步安装
    def install_sync(self,pluginInfo,get):
        import panelAuth
        try:
            token = panelAuth.panelAuth().create_serverid(None)['token']
        except:
            # return public.returnMsg(False, public.lang("Please log in as iPanel account first"))
            token = None
        if 'download' in pluginInfo['versions'][0]:
            tmp_path = '/www/server/panel/temp'
            if not os.path.exists(tmp_path): os.makedirs(tmp_path,mode=384)
            public.ExecShell("rm -rf " + tmp_path + '/*')
            toFile = tmp_path + '/' + pluginInfo['name'] + '.zip'
            public.downloadFile('{}/api/plugin/download?filename={}&token={}'.format(
                self.__official_url,
                pluginInfo['versions'][0]['download'],
                token
                ),toFile)
            if public.FileMd5(toFile) != pluginInfo['versions'][0]['md5']: return public.return_msg_gettext(False, public.lang("File hash verification failed, stop installation!"))
            update = False
            if os.path.exists(pluginInfo['install_checks']): update =pluginInfo['versions'][0]['version_msg']
            return self.update_zip(None,toFile,update)
        else:
            # download_url = public.get_url() + '/install/plugin/' + pluginInfo['name'] + '_en/install.sh'
            # toFile = '/tmp/%s.sh' % pluginInfo['name']
            # public.downloadFile(download_url,toFile)
            # self.set_pyenv(toFile)
            # public.ExecShell('/bin/bash ' + toFile + ' install &> /tmp/panelShell.pl')
            # if os.path.exists(pluginInfo['install_checks']):
            #     public.write_log_gettext('Installer','Successfully installed plugin [{}]',(pluginInfo['title'],))
            #     if os.path.exists(toFile): os.remove(toFile)
            #     return public.return_msg_gettext(True, public.lang("Installation succeeded!"))
            # return public.return_msg_gettext(False, public.lang("Installation failed"))

            if hasattr(get, 'min_version'):
                get.version += '.' + get.min_version

            return self.__install_plugin(pluginInfo['name'], get.version)

    # 设置Python环境变量
    def set_pyenv(self, filename):
        if not os.path.exists(filename): return False
        env_py = '/www/server/panel/pyenv/bin'
        if not os.path.exists(env_py): return False
        temp_file = public.readFile(filename)
        env_path = ['PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin']
        rep_path = ['PATH={}/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin'.format(env_py + ":")]
        for i in range(len(env_path)):
            temp_file = temp_file.replace(env_path[i], rep_path[i])
        public.writeFile(filename, temp_file)
        return True

    #异步安装
    def install_async(self,pluginInfo,get):
        # # 只取主版本号与子版本号，忽略修订号
        # if 'version' in get:
        #     get.version = '.'.join(str(get.version).split('.')[:2])

        mtype = 'install'
        mmsg = public.lang("Install")
        if hasattr(get, 'upgrade'):
            mtype = 'update'
            mmsg = 'upgrade'
        if not 'type' in get: get.type = '0'
        if int(get.type) > 4: get.type = '0'
        if get.sName == 'nginx':
            if get.version == '1.8': return public.return_msg_gettext(False, public.lang("Nginx 1.8.1 is too old, no longer available, please choose another version!"))
        if get.sName.find('php-') != -1:get.sName = get.sName.split('-')[0]
        ols_execstr = ""
        if "php" == get.sName and os.path.exists('/usr/local/lsws/bin/lswsctrl'):
            ols_sName = 'php-ols'
            ols_version = get.version.replace('.','')
            ols_execstr = " &> /tmp/panelExec.log && /bin/bash install_soft.sh {} {} " + ols_sName + " " + ols_version
        php_path = '/www/server/php'
        if not os.path.exists(php_path): os.makedirs(php_path)
        apacheVersion='false'
        if public.get_webserver() == 'apache':
            apacheVersion = public.xss_version(public.readFile('/www/server/apache/version.pl'))
        public.writeFile('/var/bt_apacheVersion.pl',apacheVersion)
        public.writeFile('/var/bt_setupPath.conf','/www')
        if os.path.exists('/usr/bin/apt-get'):
            if get.type == '0':
                get.type = '3'
            else:
                get.type = '4'
        if ols_execstr:
            ols_execstr = ols_execstr.format(get.type,mtype)
        execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh {} {} {} {} {}".format(
            get.type, mtype, get.sName, get.version, ols_execstr)
        if get.sName == "phpmyadmin":
            # 当面板开启SSL时，标记下次打开phpmyadmin时需要设置SSL
            if os.path.exists('{}/data/ssl.pl'.format(public.get_panel_path())):
                with open('{}/data/phpmyadmin_ssl.mark'.format(public.get_panel_path()), 'w') as fp:
                    fp.write('1')

            execstr += "&> /tmp/panelExec.log"
        if public.get_webserver() == 'openlitespeed':
            execstr += " && sleep 1 && /usr/local/lsws/bin/lswsctrl restart"
        # 清理日志文件
        if os.path.exists("/tmp/panelExec.log"):
            public.writeFile("/tmp/panelExec.log","")
        public.M('tasks').add('id,name,type,status,addtime,execstr',(None, mmsg + '['+get.sName+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        cache.delete('install_task')
        public.writeFile('/tmp/panelTask.pl','True')
        public.write_log_gettext('Installer','Successfully added intallation task [{}-{}]',(get.sName,get.version))
        return public.return_msg_gettext(True, public.lang("Installation task added to queue"))

    #卸载插件
    def uninstall_plugin(self,get):
        pluginInfo = self.get_soft_find(get.sName)
        if not pluginInfo: return public.return_msg_gettext(False, public.lang("The specified plugin does not exist!"))
        if pluginInfo['type'] != 5:
            pluginPath = self.__install_path + '/' + pluginInfo['name']
            if pluginInfo['type'] != 6:
                download_url = session['download_url'] + '/install/plugin/' + pluginInfo['name'] + '_en/install.sh'
                toFile = '/tmp/%s.sh' % pluginInfo['name']
                public.downloadFile(download_url,toFile)
                self.set_pyenv(toFile)
                if os.path.exists(toFile):
                    if os.path.getsize(toFile) > 100:
                        public.ExecShell('/bin/bash ' + toFile + ' uninstall')

            if os.path.exists(pluginPath + '/install.sh'):
                self.set_pyenv(pluginPath + '/install.sh')
                public.ExecShell('/bin/bash ' + pluginPath + '/install.sh uninstall')

            if os.path.exists(pluginPath): public.ExecShell('rm -rf ' + pluginPath)
            public.write_log_gettext('Installer','Successfully uninstalled software [{}]',(pluginInfo['title'],))
            return public.return_msg_gettext(True, public.lang("Uninstallaton succeeded"))
        else:

            if pluginInfo['name'] == 'mysql':
                if public.M('databases').where('db_type=?',0).count() > 0: return public.return_msg_gettext(False, public.lang("The database list is not empty. For your data security, please backup and delete the existing database.<br>Forced uninstall command: rm -rf /www/server/mysql"))
            if pluginInfo['name'] == 'nginx':
                import nginx
                nginx.nginx().del_all_log_format(get)
            if pluginInfo['name'] == 'apache':
                import apache
                apache.apache().del_all_log_format(get)
            get.type = '0'
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            get.sName = get.sName.lower()
            if get.sName.find('php-') != -1:
                get.sName = get.sName.split('-')[0]
            execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh "+get.type+" uninstall " + get.sName.lower() + " "+ get.version.replace('.','')
            public.ExecShell(execstr)
            public.write_log_gettext('Installer','Successfully unintalled [{}-{}]',(get.sName,get.version))
            return public.return_msg_gettext(True, public.lang("Uninstallation succeeded"))

    #从云端取列表
    def get_cloud_list(self, get=None):
        force = 0
        if get and hasattr(get, 'force'):
            force = int(get.force)

        if 'focre_cloud' in session:
            if session['focre_cloud']:
                force = 1
                session['focre_cloud'] = False

        if 'init_cloud' not in session:
            force = 1
            session['init_cloud'] = True

        softList = public.load_soft_list(True if force == 1 else False)


        if get and 'init' in get:
            if softList:
                if 'success' not in softList:
                    return softList

        if force > 0:
            public.ExecShell('rm -f /tmp/bmac_*')
            public.run_thread(self.getCloudPHPExt)
            # 专业版和企业版到期提醒，iPanel目前没有先注释
            # self.expire_msg(softList)

        try:
            p_token = cache.get('p_token')

            if p_token is None:
                p_token = 'bmac_' + public.Md5(public.get_mac_address())
                cache.set('p_token', p_token)

            public.writeFile("/tmp/" + p_token, str(softList['pro']))
            public.writeFile('/tmp/{}.time'.format(p_token), str(int(time.time())))
        except:
            pass

        sType = 0
        try:
            if hasattr(get,'type'): sType = int(get['type'])
            if hasattr(get,'query'):
                if get.query:
                    # 关键词统计     参数keyword
                    import panelAuth
                    import requests
                    countUrl = '{}/api/panel/submit_keyword'.format(self.__official_url)
                    pdata = panelAuth.panelAuth().create_serverid(None)
                    url_headers = {}
                    if 'token' in pdata:
                        url_headers = {"authorization": "bt {}".format(pdata['token'])}
                    pdata['environment_info'] = json.dumps(public.fetch_env_info())
                    keyword = {
                        "keyword": get.query
                    }
                    try:
                        requests.post(countUrl, params=keyword, headers=url_headers, verify=False, timeout=3)
                    except:
                        pass
                    sType = 0
        except:pass

        # 扫描本地插件并追加到软件列表中
        softList['list'] = self.get_local_plugin(softList['list'])

        # 软件列表分类处理
        softList['list'] = self.get_types(softList['list'], sType)

        if hasattr(get, 'query'):
            if get.query:
                get.query = get.query.lower()
                tmpList = []
                for softInfo in softList['list']:
                    if softInfo['name'].lower().find(get.query) != -1 or \
                        softInfo['title'].lower().find(get.query) != -1 or \
                        softInfo['ps'].lower().find(get.query) != -1:
                        tmpList.append(softInfo)
                softList['list'] = tmpList

        for softInfo in softList['list']:
            if 'uninsatll_checks' not in softInfo:
                softInfo['uninsatll_checks'] = softInfo['uninstall_checks']

        return softList

    #取提醒标记
    def get_level_msg(self,level,s_time,endtime):
        '''
            level 提醒标记
            s_time 当前时间戳
            endtime 到期时间戳
        '''
        expire_day = (endtime - s_time) / 86400
        if expire_day < 15 and expire_day > 7:
            level = level + '15'
        elif expire_day < 7 and expire_day > 3:
            level = level + '7'
        elif expire_day < 3 and expire_day > 0:
            level = level + '3'
        return level,expire_day

    #添加到期提醒
    def add_expire_msg(self,title,level,name,expire_day,pid,endtime):
        '''
            title 软件标题
            level 提醒标记
            name 软件名称
            expire_day 剩余天数
        '''
        import panelMessage #引用消息提醒模块
        pm = panelMessage.panelMessage()
        pm.remove_message_level(level) #删除旧的提醒
        if expire_day > 15: return False
        if pm.is_level(level): #是否忽略
            if level != name: #到期还是即将到期
                msg_last = '您的【{}】授权还有{}天到期'.format(title,int(expire_day) + 1)
            else:
                msg_last = '您的【{}】授权已到期'.format(title)
            pl_msg = 'true'
            if name in ['pro','ltd']:
                pl_msg = 'false'
            renew_msg = '<a class="btlink" onclick="bt.soft.product_pay_view({name:\'%s\',pid:%s,limit:\'%s\',plugin:%s,renew:%s});">立即续费</a>' % (title,pid,name,pl_msg,endtime)
            pm.create_message(level=level,expire=7,msg="{}，为了不影响您正常使用【{}】功能，请及时续费，{}".format(msg_last,title,renew_msg))
            return True
        return False

    #到期提醒
    def expire_msg(self,data):
        '''
            data 插件列表
        '''
        s_time = time.time()
        is_plugin = True
        import panelMessage #引用消息提醒模块
        pm = panelMessage.panelMessage()
        #企业版到期提醒
        if not data['ltd'] in [-1] :

            if data['pro'] < 0 or  (data['pro'] - s_time) / 86400 < 15 :
                level,expire_day = self.get_level_msg('ltd',s_time,data['ltd'])
                print(level,expire_day)
                self.add_expire_msg('企业版',level,'ltd',expire_day,100000046,data['ltd'])
                pm.remove_message_level('pro')
                return True

        #专业版到期提醒
        if not data['pro'] in [-1,0]:
            level,expire_day = self.get_level_msg('pro',s_time,data['pro'])
            self.add_expire_msg('专业版',level,'pro',expire_day,100000030,data['pro'])
            pm.remove_message_level('ltd')
            is_plugin = False

        return True


    #提交用户评分
    def set_score(self,args):
        try:
            import panelAuth
            pdata = panelAuth.panelAuth().create_serverid(None)
            pdata['ps'] = args.ps
            pdata['num'] = int(args.num)
            pdata['pid'] = int(args.pid)
            if 1< pdata['num'] >5: return public.return_msg_gettext(False, public.lang("Scoring range [1-5]"))
            if not pdata['pid']: return public.return_msg_gettext(False, public.lang("The specified plugin does not exist!"))

            result = public.httpPost(public.GetConfigValue('home') + '/api/panel/plugin_score',pdata,10)
            result = json.loads(result)
            return result
        except:
            return public.return_msg_gettext(False, public.lang("Connection failure!"))

    #获取指定插件评分
    def get_score(self,args):
        try:
            import panelAuth
            pdata = panelAuth.panelAuth().create_serverid(None)
            pdata['pid'] = int(args.pid)
            if not pdata['pid']: return []
            u_args = ""
            sp_tip = '?'
            if 'p' in args:
                u_args += sp_tip + 'p=' + args.p
                sp_tip = '&'
            if 'tojs' in args:
                u_args += sp_tip + 'tojs='+ args.tojs
                sp_tip = '&'
            if 'limit_num' in args:
                pdata['limit_num'] = int(args.limit_num)
            result = public.httpPost(public.GetConfigValue('home') + '/api/panel/get_plugin_socre' + u_args,pdata,10)
            result = json.loads(result)
            return result
        except:
            return public.return_msg_gettext(False, public.lang("Connection failure!"))

    #清除多余面板日志
    def clean_panel_log(self):
        try:
            log_path = 'logs/request'
            if not os.path.exists(log_path): return False
            limit_num = 180
            p_logs = sorted(os.listdir(log_path))
            num = len(p_logs) - limit_num
            if num > 0:
                for i in range(num):
                    filename = log_path + '/' + p_logs[i]
                    if not os.path.exists(filename): continue
                    os.remove(filename)

            today = public.getDate(format='%Y-%m-%d')
            for fname in os.listdir(log_path):
                fsplit = fname.split('.')
                if fsplit[-1] != 'json':
                    continue
                if fsplit[0] == today:
                    continue
                public.ExecShell("cd {} && gzip {}".format(log_path,fname))

            #清理错误日志
            public.clean_max_log('/www/server/panel/logs/error.log',10,20)
            public.clean_max_log('/www/server/panel/logs/socks5.log',10,20)
            public.clean_max_log('/www/server/panel/logs/oos.log',10,20)
            return True
        except:return False

    #取本地插件
    def get_local_plugin(self,sList):
        for name in os.listdir('plugin/'):
            isExists = False
            for softInfo in sList:
                if name == softInfo['name']:
                    isExists = True
                    break
            if isExists: continue
            filename = 'plugin/' + name + '/info.json'
            if not os.path.exists(filename): continue
            tmpInfo = public.ReadFile(filename).strip()
            if not tmpInfo: continue
            try:
                info = json.loads(tmpInfo)
            except: continue
            pluginInfo = self.get_local_plugin_info(info)
            if not pluginInfo: continue
            sList.append(pluginInfo)
        return sList

    #检查是否正在安装
    def check_setup_task(self,sName):
        if not self.__tasks:
            self.__tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        if sName.find('php-') != -1:
            tmp = sName.split('-')
            sName = tmp[0]
            version = tmp[1]
        isTask = '1'
        for task in self.__tasks:
            tmpt = public.getStrBetween('[',']',task['name'])
            if not tmpt:continue
            tmp1 = tmpt.split('-')
            name1 = tmp1[0].lower()
            if sName == 'php':
                if name1 != sName or tmp1[1] != version: continue
                isTask = task['status']
            else:
                if name1 == 'pure': name1 = 'pure-ftpd'
                if name1 != sName: continue
                isTask = task['status']

            if isTask == '-1' or isTask == '0':
                if task['name'].find('upgrade') != -1: isTask = '-2'
            break
        return isTask


    #构造本地插件信息
    def get_local_plugin_info(self,info):
        m_version = info['versions'].split(".")
        if len(m_version) < 2: return None
        if len(m_version) > 2:
            tmp = m_version[:]
            del(tmp[0])
            m_version[1] = '.'.join(tmp)

        try:
            if not 'author' in info: info['author'] = '未知'
            if not 'home' in info: info['home'] = '#'
            pluginInfo = {
	                        "id": 10000,
	                        "pid": 0,
	                        "type": 10,
	                        "price": 0,
                            "author":info['author'],
                            "home":info['home'],
	                        "name": info['name'],
	                        "title": info['title'],
	                        "panel_pro": 1,
	                        "panel_free": 1,
	                        "panel_test": 1,
	                        "ps": info['ps'],
	                        "version": info['versions'],
	                        "s_version": "0",
	                        "manager_version": "1",
	                        "c_manager_version": "1",
	                        "dependent": "",
	                        "mutex": "",
	                        "install_checks": "/www/server/panel/plugin/" + info['name'],
	                        "uninsatll_checks": "/www/server/panel/plugin/" + info['name'],
	                        "compile_args": 0,
	                        "version_coexist": 0,
	                        "versions": [
		                        {
			                        "m_version": m_version[0],
			                        "version": m_version[1],
			                        "dependent": "",
			                        "mem_limit": 32,
			                        "cpu_limit": 1,
			                        "os_limit": 0,
			                        "setup": True
		                        }
	                        ],
	                        "setup": True,
	                        "status": True
                        }
        except: pluginInfo = None
        return pluginInfo

    #处理分类
    def get_types(self,sList,sType):
        if sType <= 0: return sList
        sType = [sType]
        # if sType != 12:
        #     sType = [sType]
        # else:
        #     sType = [sType,8]
        newList = []
        for sInfo in sList:
            if int(sInfo['type']) in sType: newList.append(sInfo)
        return newList

    #检查权限
    def check_accept(self,get):
        args = public.dict_obj()
        args.type = '8'
        p_list = self.get_cloud_list(args)
        for p in p_list['list']:
            if p['name'] == get.name:
                if int(p_list['pro']) < 0 and int(p['endtime']) < 0: return False
                break

        args.type = '10'
        p_list = self.get_cloud_list(args)
        for p in p_list['list']:
            if p['name'] == get.name:
                if not 'endtime' in p: continue
                if int(p['endtime']) < 0: return False
                break

        args.type = '12'
        p_list = self.get_cloud_list(args)
        for p in p_list['list']:
            if not p['type'] in [12,'12']: continue
            if p['name'] == get.name:
                if not 'endtime' in p: continue
                if int(p_list['ltd']) < 1 and int(p['endtime']) < 1: return False
                break
        return True

    #取软件列表
    def get_soft_list(self,get = None):
        softList = self.get_cloud_list(get)
        if not softList:
            get.force = 1
            softList = self.get_cloud_list(get)
            if not softList: return public.return_msg_gettext(False,public.lang('Failed to get software list ({})',"401"))
        softList['list'] = self.set_coexist(softList['list'])
        if not 'type' in get: get.type = '0'
        if get.type == '-1':
            soft_list_tmp = []
            softList['list'] = self.check_isinstall(softList['list'])
            for val in softList['list']:
                if 'setup' in val:
                    if val['setup']: soft_list_tmp.append(val)
            softList['list'] = soft_list_tmp
            softList['list'] = self.get_page(softList['list'],get)
        else:
            softList['list'] = self.get_page(softList['list'],get)
            softList['list']['data'] = self.check_isinstall(softList['list']['data'])
        softList['apache22'] = False
        softList['apache24'] = False
        check_version_path = '/www/server/apache/version_check.pl'
        if os.path.exists(check_version_path):
            softList['apache24'] = True
            if public.readFile(check_version_path).find('2.2') == 0:
                softList['apache22'] = True
                softList['apache24'] = False
        return softList

    #取首页软件列表
    def get_index_list(self, get=None):
        softList = self.get_cloud_list(get)['list']
        if not softList:
            get.force = 1
            softList = self.get_cloud_list(get)['list']
            if not softList: return public.return_msg_gettext(False,public.lang('Failed to get software list ({})',"401"))
        softList = self.set_coexist(softList)
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        try:
            indexList = json.loads(public.ReadFile(self.__index))
        except Exception:
            os.remove(self.__index)
            public.writeFile(self.__index, '[]')
            indexList = []
        dataList = []
        for index in indexList:
            for softInfo in softList:
                if softInfo['name'] == index: dataList.append(softInfo)
        dataList = self.check_isinstall(dataList)

        return dataList

    #添加到首页
    def add_index(self,get):
        sName = get.sName
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        if sName in indexList: return public.return_msg_gettext(False, public.lang("Please do NOT repeat adding"))
        if len(indexList) >= 12:
            softList = self.get_cloud_list(get)['list']
            softList = self.set_coexist(softList)
            for softInfo in softList:
                # return softList
                if softInfo['name'] == 'php':
                    for i in softInfo['versions']:
                        php_v = 'php-'+ i['m_version']
                        if not os.path.exists('/www/server/php/{}'.format(i['m_version']))\
                                and php_v in indexList:
                            indexList.remove(php_v)
                if softInfo['name'] in indexList:
                    new_softInfo = self.check_status(softInfo)
                    if not new_softInfo['setup']: indexList.remove(softInfo['name'])
            public.writeFile(self.__index,json.dumps(indexList))
            if len(indexList) >= 12: return public.return_msg_gettext(False, public.lang("Dashboard only display up to 12 software!"))
        indexList.append(sName)
        public.writeFile(self.__index,json.dumps(indexList))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    #删除首页
    def remove_index(self,get):
        sName = get.sName
        indexList = []
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        if not sName in indexList: return public.return_msg_gettext(True, public.lang("Successfully deleted!"))
        indexList.remove(sName)
        public.writeFile(self.__index,json.dumps(indexList))
        return public.return_msg_gettext(True, public.lang("Successfully deleted!"))

    #设置排序
    def sort_index(self,get):
        indexList = get.ssort.split('|')
        public.writeFile(self.__index,json.dumps(indexList))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    #取快捷软件列表
    def get_link_list(self,get=None):
        softList = self.get_cloud_list(get)['list']
        softList = self.set_coexist(softList)
        indexList = json.loads(public.ReadFile(self.__link))
        dataList = []
        for index in indexList:
            for softInfo in softList:
                if softInfo['name'] == index: dataList.append(softInfo)
        dataList = self.check_isinstall(dataList)
        return dataList

    #添加到快捷栏
    def add_link(self,get):
        sName = get.sName
        indexList = json.loads(public.ReadFile(self.__link))
        if sName in indexList: return public.return_msg_gettext(False, public.lang("Please do NOT repeat adding"))
        if len(indexList) >= 5: return public.return_msg_gettext(False, public.lang("Shortcut Bar only display up to 5 software!"))
        indexList.append(sName)
        public.writeFile(self.__link,json.dumps(indexList))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    #删除快捷栏
    def remove_link(self,get):
        sName = get.sName
        indexList = []
        indexList = json.loads(public.ReadFile(self.__link))
        if sName in indexList: return public.return_msg_gettext(True, public.lang("Successfully deleted!"))
        indexList.remove(sName)
        public.writeFile(self.__link,json.dumps(indexList))
        return public.return_msg_gettext(True, public.lang("Successfully deleted!"))

    #设置快捷栏排序
    def sort_link(self,get):
        indexList = get.ssort.split('|')
        public.writeFile(self.__link,json.dumps(indexList))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))



    #处理共存软件
    def set_coexist(self,sList):
        softList = []
        for sInfo in sList:
            try:
                if sInfo['version_coexist'] == 1 and 'versions' in sInfo:
                    for versionA in sInfo['versions']:
                        try:
                            sTmp = sInfo.copy()
                            v = versionA['m_version'].replace('.','')
                            sTmp['title'] = sTmp['title']+'-'+versionA['m_version']
                            sTmp['name'] = sTmp['name']+'-'+versionA['m_version']
                            sTmp['version'] = sTmp['version'].replace('{VERSION}',v)
                            sTmp['manager_version'] = sTmp['manager_version'].replace('{VERSION}',v)
                            sTmp['install_checks'] = sTmp['install_checks'].replace('{VERSION}',v)
                            if 'uninsatll_checks' not in sTmp:
                                sTmp['uninsatll_checks'] = sTmp['uninstall_checks'].replace('{VERSION}',v)
                            else:
                                sTmp['uninsatll_checks'] = sTmp['uninsatll_checks'].replace('{VERSION}',v)
                            sTmp['s_version'] = sTmp['s_version'].replace('{VERSION}',v)
                            sTmp['versions'] = []
                            sTmp['versions'].append(versionA)
                            softList.append(sTmp)
                        except: continue
                else:
                    softList.append(sInfo)
            except: continue
        return softList

    #检测是否安装
    def check_isinstall(self,sList):
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        for i in range(len(sList)):
            sList[i]['index_display'] = sList[i]['name'] in indexList
            sList[i] = self.check_status(sList[i])
        return sList


    #检查软件状态
    def check_status(self,softInfo):
        softInfo['setup'] = os.path.exists(softInfo['install_checks'])
        softInfo['status'] = False
        softInfo['task'] = self.check_setup_task(softInfo['name'])
        if softInfo['name'].find('php-') != -1: softInfo['fpm'] = False
        if softInfo['setup']:
            softInfo['shell'] = softInfo['version']
            softInfo['version'] = self.get_version_info(softInfo)
            softInfo['status'] = True
            softInfo['versions'] = self.tips_version(softInfo['versions'],softInfo['version'])
            softInfo['admin'] = os.path.exists('/www/server/panel/plugin/' + softInfo['name'])

            if 's_version' in softInfo and len(softInfo['s_version']) > 3:
                pNames = softInfo['s_version'].split(',')
                for pName in pNames:
                    if len(softInfo['manager_version']) > 5:
                        softInfo['status'] = self.process_exists(pName,softInfo['manager_version'])
                    else:
                        softInfo['status'] = self.process_exists(pName)
                    if softInfo['status']: break
        else:
            softInfo['version'] = ""
        if softInfo['version_coexist'] == 1:
            if softInfo['id'] != 10000:
                self.get_icon(softInfo['name'].split('-')[0])
        else:
            if 'min_image' in softInfo:
                if softInfo['id'] != 10000:
                    self.get_icon(softInfo['name'],softInfo['min_image'])
            else:
                # if softInfo['id'] != 10000:
                self.get_icon(softInfo['name'])

        if softInfo['name'].find('php-') != -1:
            v2= softInfo['versions'][0]['m_version'].replace('.','')
            softInfo['fpm'] = os.path.exists('/www/server/php/' + v2 + '/sbin/php-fpm')
            softInfo['status'] = self.get_php_status(v2)
            pid_file = '/www/server/php/' + v2 + '/var/run/php-fpm.pid'
            if not softInfo['fpm']:
                softInfo['status'] = True
            elif softInfo['status'] and os.path.exists(pid_file):
                try:
                    softInfo['status'] = public.pid_exists(int(public.readFile(pid_file)))
                except:
                    if os.path.exists(pid_file):
                        os.remove(pid_file)

        if softInfo['name'] == 'mysql':
            softInfo['status'] = self.process_exists('mysqld')
            if not softInfo['status']: softInfo['status'] = self.process_exists('mariadbd')
        if softInfo['name'] == 'phpmyadmin': softInfo['status'] = self.get_phpmyadmin_stat()
        if softInfo['name'] == 'openlitespeed':
            pid_file = '/run/openlitespeed.pid'
            if os.path.exists(pid_file):
                pid = int(public.readFile(pid_file))
                softInfo['status'] = public.pid_exists(pid)
        return softInfo

    def get_php_status(self,phpversion):
        '''
            @name 获取指定PHP版本的服务状态
            @author hwliang<2020-10-23>
            @param phpversion string PHP版本
            @return bool
        '''
        try:
            php_status = os.path.exists('/tmp/php-cgi-'+phpversion+'.sock')
            if php_status: return php_status
            pid_file = '/www/server/php/{}/var/run/php-fpm.pid'.format(phpversion)
            if not os.path.exists(pid_file): return False
            pid = int(public.readFile(pid_file))
            return os.path.exists('/proc/{}/comm'.format(pid))
        except:
            return False




    #取phpmyadmin状态
    def get_phpmyadmin_stat(self):
        webserver = public.get_webserver()
        if webserver == 'nginx':
            filename = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
        elif webserver == 'apache':
            filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
        else:
            filename = "/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        if not os.path.exists(filename): return False
        conf = public.readFile(filename)
        if not conf: return False
        is_start = conf.find('/www/server/stop') == -1
        if is_start:
            if webserver == 'nginx':
                is_start = conf.find('allow 127.0.0.1;') == -1
            elif webserver == 'apache':
                is_start = conf.find('Allow from 127.0.0.1 ::1 localhost') == -1
        return is_start


    #获取指定软件信息
    def get_soft_find(self,get = None):
        if not self.__plugin_s_list:
            softList = self.get_cloud_list(get)['list']
            self.__plugin_s_list = self.set_coexist(softList)

        try:
            sName = get['sName']
        except:
            sName = get

        for softInfo in self.__plugin_s_list:

            if softInfo['name'] == sName:
                if sName == 'phpmyadmin':
                    # 检查是否需要开启SSL
                    if os.path.exists('{}/data/phpmyadmin_ssl.mark'.format(public.get_panel_path())) and os.path.exists('{}/phpmyadmin'.format(public.get_setup_path())):
                        os.remove('{}/data/phpmyadmin_ssl.mark'.format(public.get_panel_path()))
                        from ajax_v2 import ajax
                        ajax().set_phpmyadmin_ssl(public.to_dict_obj({'v': '1'}))

                    from BTPanel import get_phpmyadmin_dir
                    pmd = get_phpmyadmin_dir()
                    softInfo['ext'] = self.getPHPMyAdminStatus()
                    if softInfo['ext'] and pmd:
                        port = softInfo['ext']['ssl_port'] if softInfo['ext'].get('ssl_enabled', False) else pmd[1]
                        softInfo['ext']['url'] = 'http' + ('s' if softInfo['ext'].get('ssl_enabled', False) else '') + '://' + public.GetHost() + ':'+ port + '/' + pmd[0]
                if "php-" in sName:
                    v = softInfo["versions"][0]["m_version"]
                    v1 = v.replace(".", "")
                    if public.get_webserver() == "openlitespeed":
                        softInfo["php_ini"] = "/usr/local/lsws/lsphp{}/etc/php/{}/litespeed/php.ini".format(v1, v)
                        if os.path.exists("/etc/redhat-release"):
                            softInfo["php_ini"] = "/usr/local/lsws/lsphp{}/etc/php.ini".format(v1)
                    else:
                        softInfo["php_ini"] = "/www/server/php/{}/etc/php.ini".format(v1)

                return self.check_status(softInfo)

        return False


    #获取版本信息
    def get_version_info(self,sInfo):
        version = ''
        vFile1 = sInfo['uninsatll_checks'] + '/version_check.pl'
        vFile2 = sInfo['uninsatll_checks'] + '/info.json'
        if os.path.exists(vFile1):
            version = public.xss_version(public.ReadFile(vFile1).strip())
            if not version: os.remove(vFile1)
        elif  os.path.exists(vFile2):
            v_tmp = public.ReadFile(vFile2).strip()
            if v_tmp:
                try:
                    version = json.loads(v_tmp)['versions']
                except: public.ExecShell('rm -f ' + vFile2)
            else:
                version = "1.0"
        else:
            exec_args = {
                    'nginx':"/www/server/nginx/sbin/nginx -v 2>&1|grep version|awk '{print $3}'|cut -f2 -d'/'",
                    'apache':"/www/server/apache/bin/httpd -v|grep version|awk '{print $3}'|cut -f2 -d'/'",
                    'mysql':"/www/server/mysql/bin/mysql -V|grep Ver|awk '{print $5}'|cut -f1 -d','",
                    'php':"/www/server/php/{VERSION}/bin/php -v|grep cli|awk '{print $2}'",
                    'pureftpd':"cat /www/server/pure-ftpd/version.pl",
                    'phpmyadmin':"cat /www/server/phpmyadmin/version.pl",
                    'tomcat':"/www/server/tomcat/bin/version.sh|grep version|awk '{print $4}'|cut -f2 -d'/'",
                    'memcached':"/usr/local/memcached/bin/memcached -V|awk '{print $2}'",
                    'redis':"/www/server/redis/src/redis-server -v|awk '{print $3}'|cut -f2 -d'='",
                    'openlitespeed': "cat /usr/local/lsws/VERSION",
                    'gitlab':'echo "8.8.5"'
                }

            exec_str = ''
            if sInfo['name'] in exec_args: exec_str = exec_args[sInfo['name']]
            if sInfo['version_coexist'] == 1:
                v_tmp = sInfo['name'].split('-')
                exec_str = exec_args[v_tmp[0]].replace('{VERSION}',v_tmp[1].replace('.',''))
            version = public.ExecShell(exec_str)[0].strip()
            if version:
                public.writeFile(vFile1,version)
            else:
                vFile4 = sInfo['uninsatll_checks'] + '/version.pl'
                if os.path.exists(vFile4):
                    version = public.xss_version(public.readFile(vFile4).strip())

        if sInfo['name'] == 'mysql':
            vFile3 = sInfo['uninsatll_checks'] + '/version.pl'
            version_str = None
            if os.path.exists(vFile3):
                version_str = public.xss_version(public.readFile(vFile3))
                if version_str.find('AliSQL') != -1: version = 'AliSQL'
            if version == 'Linux' and version_str:
                version = version_str
                public.writeFile(vFile1,version)

        if sInfo['name'] == 'nginx':
            if version.find('2.2.') != -1: version = '-Tengine' + version
        return version.replace('p1','')


    #标记当前安装的版本
    def tips_version(self,versions,version):
        if len(versions) == 1:
            versions[0]['setup'] = True
            return versions

        for i in range(len(versions)):
            if version == (versions[i]['m_version'] + '.' + versions[i]['version']):
                versions[i]['setup'] = True
                continue
            vTmp = versions[i]['m_version'].split('_')
            if len(vTmp) > 1:
                vTmp = vTmp[1]
            else:
                vTmp = vTmp[0]
            vLen = len(vTmp)
            versions[i]['setup'] = (version[:vLen] == vTmp)
        return versions

    #取pids
    def get_pids(self):
        pids = []
        for pid in os.listdir('/proc'):
            if re.match(r"^\d+$",pid): pids.append(pid)
        return pids


    #进程是否存在
    def process_exists(self,pname,exe = None):
        if pname in ['mysqld','mariadbd']:
            datadir = public.get_datadir()
            if datadir:
                pid_file = "{}/{}.pid".format(datadir,public.get_hostname())
                if os.path.exists(pid_file):
                    try:
                        pid = int(public.readFile(pid_file))
                        status = public.pid_exists(pid)
                        if status: return status
                    except:
                        return False

        if pname in ['php-fpm'] and exe:
            pid_file = exe.replace('sbin/php-fpm','/var/run/php-fpm.pid')
            if os.path.exists(pid_file):
                try:
                    pid = int(public.readFile(pid_file))
                    return public.pid_exists(pid)
                except:
                    return False

        if not self.pids: self.pids = psutil.pids()
        for pid in self.pids:
            try:
                l = '/proc/%s/exe' % pid
                f = '/proc/%s/comm' % pid
                p_exe = ''
                p_name = ''
                if os.path.exists(l):
                    p_exe = os.readlink(l)
                    if not p_name: p_name = p_exe.split('/')[-1]

                if not p_name and os.path.exists(f):
                    fp = open(f,'r')
                    p_name = fp.read().strip()
                    fp.close()

                if not p_name: continue
                if p_name == pname:
                    if not exe:
                        return True
                    else:
                        if p_exe == exe: return True
            except: continue
        return False

     #取分页
    def get_page(self,data,get):
        #包含分页类
        import page
        #实例化分页类
        page = page.Page()
        info = {}
        info['count'] = len(data)
        info['row'] = self.ROWS
        if hasattr(get,'row'):
            try:
                info['row']     = int(get['row'])
            except:
                info['row'] = self.ROWS

        info['p'] = 1
        if hasattr(get,'p'):
            try:
                info['p']     = int(get['p'])
            except:
                info['p'] = 1
        info['uri']   = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs

        #获取分页数据
        result = {}
        result['page'] = page.GetPage(info)
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n >= page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result


    #取列表
    def GetList(self,get = None):
        try:
            if not os.path.exists(self.__list): return []
            data = json.loads(public.readFile(self.__list))

            #排序
            data = sorted(data, key= lambda b:b['sort'],reverse=False)

            #获取非划分列表
            n = 0
            for dirinfo in os.listdir(self.__install_path):
                isTrue = True
                for tm in data:
                    if tm['name'] == dirinfo: isTrue = False
                if not isTrue: continue

                path = self.__install_path + '/' + dirinfo
                if os.path.isdir(path):
                    jsonFile = path + '/info.json'
                    if os.path.exists(jsonFile):
                        try:
                            tmp = json.loads(public.readFile(jsonFile))
                            if not hasattr(get,'type'):
                                get.type = 0
                            else:
                                get.type = int(get.type)

                            if get.type > 0:
                                try:
                                    if get.type != tmp['id']: continue
                                except:
                                    continue

                            tmp['pid'] = len(data) + 1000 + n
                            tmp['status'] = tmp['display']
                            tmp['display'] = 0
                            data.append(tmp)
                        except:
                            pass
            #索引列表
            if get:
                display = None
                if hasattr(get,'display'): display = True
                if not hasattr(get,'type'):
                    get.type = 0
                else:
                    get.type = int(get.type)
                if not hasattr(get,'search'):
                    search = None
                    m = 0
                else:
                    search = get.search.encode('utf-8').lower()
                    m = 1

                tmp = []
                for d in data:
                    if d['id'] != 10000:
                        self.get_icon(d['name'])
                    if display:
                        if d['display'] == 0: continue
                    i=0
                    if get.type > 0:
                        if get.type == d['id']: i+=1
                    else:
                        i+=1
                    if search:
                        if d['name'].lower().find(search) != -1: i+=1
                        if d['name'].find(search) != -1: i+=1
                        if d['title'].lower().find(search) != -1: i+=1
                        if d['title'].find(search) != -1: i+=1
                        if get.type > 0 and get.type != d['type']: i -= 1
                    if i>m:tmp.append(d)
                data = tmp
            return data
        except Exception as ex:
            return str(ex)


    #获取图标
    def get_icon(self,name,downFile = None):
        iconFile = 'BTPanel/static/img/soft_ico/ico-' + name + '.png'
        if not os.path.exists(iconFile):
            public.run_thread(self.download_icon,(name,iconFile,downFile))
        else:
            size = os.path.getsize(iconFile)
            if size == 0:
                public.run_thread(self.download_icon,(name,iconFile,downFile))
                # self.download_icon(name,iconFile,downFile)

    #下载图标
    def download_icon(self,name,iconFile,downFile):
        srcIcon =  'plugin/' + name + '/icon.png'
        skey = name+'_icon'
        if cache.get(skey): return None
        if os.path.exists(srcIcon):
            public.ExecShell(r"\cp  -a -r " + srcIcon + " " + iconFile)
        else:
            if downFile:
                public.ExecShell('wget -O ' + iconFile + ' ' + public.GetConfigValue('home') + downFile + " &")
            else:
                public.ExecShell('wget -O ' + iconFile + ' ' + public.get_url() + '/install/plugin/' + name + '/icon.png' + " &")
        cache.set(skey,1,86400)


    #取分页
    def GetPage(self,data,get):
        #包含分页类
        import page
        #实例化分页类
        page = page.Page()
        info = {}
        info['count'] = len(data)
        info['row']   = self.ROWS
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']     = int(get['p'])
        info['uri']   = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs

        #获取分页数据
        result = {}
        result['page'] = page.GetPage(info)
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n > page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result

    #取分类
    def GetType(self,get = None):
        try:
            if not os.path.exists(self.__type): return False
            data = json.loads(public.readFile(self.__type))
            return data
        except:
            return False

    #取单个
    def GetFind(self,name):
        try:
            data = self.GetList(None)
            for d in data:
                if d['name'] == name: return d
            return None
        except:
            return None

    #设置
    def SetField(self,name,key,value):
        data = self.GetList(None)
        for i in range(len(data)):
            if data[i]['name'] != name: continue
            data[i][key] = value

        public.writeFile(self.__list,json.dumps(data))
        return True



    #安装插件
    def install(self,get):
        pluginInfo = self.GetFind(get.name)
        if not pluginInfo:
            import json
            pluginInfo = json.loads(public.readFile(self.__install_path + '/' + get.name + '/info.json'))

        if pluginInfo['tip'] == 'lib':
            if not os.path.exists(self.__install_path + '/' + pluginInfo['name']): public.ExecShell('mkdir -p ' + self.__install_path + '/' + pluginInfo['name'])
            if not 'download_url' in session: session['download_url'] = public.get_url()
            download_url = session['download_url'] + '/install/plugin/' + pluginInfo['name'] + '/install.sh'
            toFile = self.__install_path + '/' + pluginInfo['name'] + '/install.sh'
            public.downloadFile(download_url,toFile)
            self.set_pyenv(toFile)
            public.ExecShell('/bin/bash ' + toFile + ' install')
            if self.checksSetup(pluginInfo['name'],pluginInfo['checks'],pluginInfo['versions'])[0]['status'] or os.path.exists(self.__install_path + '/' + get.name):
                public.write_log_gettext('Installer','Successfully installed plugin [{}]',(pluginInfo['title'],))
                #public.ExecShell('rm -f ' + toFile);
                return public.return_msg_gettext(True, public.lang("Installation succeeded!"))
            return public.return_msg_gettext(False, public.lang("Installation failed!"))
        else:
            import db,time
            path = '/www/server/php'
            if not os.path.exists(path): public.ExecShell("mkdir -p " + path)
            issue = public.readFile('/etc/issue')
            if session['server_os']['x'] != 'RHEL': get.type = '3'

            apacheVersion='false'
            if public.get_webserver() == 'apache':
                apacheVersion = public.xss_version(public.readFile('/www/server/apache/version.pl'))
            public.writeFile('/var/bt_apacheVersion.pl',apacheVersion)
            public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
            isTask = '/tmp/panelTask.pl'

            mtype = 'install'
            mmsg = 'install'
            if hasattr(get, 'upgrade'):
                if get.upgrade:
                    mtype = 'update'
                    mmsg = 'upgrade'
            execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh " + get.type + " "+mtype+" " + get.name + " "+ get.version;
            sql = db.Sql()
            if hasattr(get,'id'):
                id = get.id
            else:
                id = None
            sql.table('tasks').add('id,name,type,status,addtime,execstr',(None, mmsg + '['+get.name+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
            public.writeFile(isTask,'True')
            public.write_log_gettext('Installer','Successfully added intallation task [{}-{}]',(get.name,get.version))
            return public.return_msg_gettext(True, public.lang("Installation task added to queue"))


    #卸载插件
    def unInstall(self,get):
        pluginInfo = self.GetFind(get.name)
        if not pluginInfo:
            import json
            pluginInfo = json.loads(public.readFile(self.__install_path + '/' + get.name + '/info.json'))
        if pluginInfo['tip'] == 'lib':
            if not os.path.exists(self.__install_path+ '/' + pluginInfo['name']): public.ExecShell('mkdir -p ' + self.__install_path + '/' + pluginInfo['name'])
            download_url = session['download_url'] + '/install/plugin/' + pluginInfo['name'] + '/install.sh'
            toFile = self.__install_path + '/' + pluginInfo['name'] + '/uninstall.sh'
            install_sh = self.__install_path + '/' + pluginInfo['name'] + '/install.sh'
            if not os.path.exists(toFile) and not os.path.exists(install_sh):
                public.downloadFile(download_url,toFile)
                self.set_pyenv(toFile)

            pluginPath = self.__install_path + '/' + pluginInfo['name']

            if os.path.exists(toFile):
                public.ExecShell('/bin/bash {} uninstall'.format(toFile))
            elif os.path.exists(pluginPath + '/install.sh'):
                public.ExecShell('/bin/bash ' + pluginPath + '/install.sh uninstall')

            if os.path.exists(pluginPath):
                public.ExecShell('rm -rf ' + pluginPath)

            public.write_log_gettext('Installer','Successfully uninstalled software [{}]',(pluginInfo['title'],))
            return public.return_msg_gettext(True, public.lang("Uninstallation succeeded"))
        else:
            get.type = '0'
            issue = public.readFile('/etc/issue')
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
            execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh "+get.type+" uninstall " + get.name.lower() + " "+ get.version.replace('.','')
            public.ExecShell(execstr)
            public.WriteLog('TYPE_SETUP','Successfully uninstalled [{}-{}]',(get.name,get.version))
            return public.returnMsg(True, public.lang("Uninstallation succeeded"))

    #取产品信息
    def getProductInfo(self,productName):
        if not self.__product_list:
            import panelAuth
            Auth = panelAuth.panelAuth()
            self.__product_list = Auth.get_business_plugin(None)
        for product in self.__product_list:
            if product['name'] == productName: return product
        return None

    #取到期时间
    def getEndDate(self,pluginName):
        if not self.__plugin_list:
            import panelAuth
            Auth = panelAuth.panelAuth()
            tmp = Auth.get_plugin_list(None)
            if not tmp: return public.lang("NOT opened")
            if not 'data' in tmp: return public.lang("NOT opened")
            self.__plugin_list = tmp['data']
        for pluinfo in self.__plugin_list:
            if pluinfo['product'] == pluginName:
                if not pluinfo['endtime'] or not pluinfo['state']: return public.lang("To be paid")
                if pluinfo['endtime'] < time.time(): return public.lang("Expired")
                return time.strftime("%Y-%m-%d",time.localtime(pluinfo['endtime']));
        return public.lang("NOT opened")

    #取插件列表
    def getPluginList(self,get):
        import json
        arr = self.GetList(get)
        result = {}
        if not arr:
            result['data'] = arr
            result['type'] = self.GetType(None)
            return result
        apacheVersion = ""
        try:
            apavFile = '/www/server/apache/version.pl'
            if os.path.exists(apavFile):
                apacheVersion = public.xss_version(public.readFile(apavFile).strip())
        except:
            pass

        result = self.GetPage(arr,get)
        arr = result['data']
        for i in range(len(arr)):
            arr[i]['end'] = '--'
            #if 'price' in arr[i]:
            #    if arr[i]['price'] > 0:
            #        arr[i]['end'] = self.getEndDate(arr[i]['title']);
            #        if os.path.exists('plugin/beta/config.conf'):
            #            if os.path.exists('plugin/' + arr[i]['name'] + '/' + arr[i]['name'] + '_main.py') and arr[i]['end'] == '未开通': arr[i]['end'] = '--';


            if arr[i]['name'] == 'php':
                if apacheVersion == '2.2':
                    arr[i]['versions'] = '5.2,5.3,5.4'
                    arr[i]['update'] = self.GetPv(arr[i]['versions'], arr[i]['update'])
                elif apacheVersion == '2.4':
                    arr[i]['versions'] = '5.3,5.4,5.5,5.6,7.0,7.1,7.2,7.3,7.4'
                    arr[i]['update'] = self.GetPv(arr[i]['versions'], arr[i]['update'])
                arr[i]['apache'] = apacheVersion

            arr[i]['versions'] = self.checksSetup(arr[i]['name'].replace('_soft',''),arr[i]['checks'],arr[i]['versions'])

            try:
                arr[i]['update'] = arr[i]['update'].split(',')
            except:
                arr[i]['update'] = []

            #是否强制使用插件模板 LIB_TEMPLATE
            if os.path.exists(self.__install_path+'/'+arr[i]['name']): arr[i]['tip'] = 'lib'

            if arr[i]['tip'] == 'lib':
                arr[i]['path'] = self.__install_path + '/' + arr[i]['name'].replace('_soft','')
                arr[i]['config'] = os.path.exists(arr[i]['path'] + '/index.html')
            else:
                arr[i]['path'] = '/www/server/' + arr[i]['name'].replace('_soft','')
        arr.append(public.M('tasks').where("status!=?",('1',)).count())


        result['data'] = arr
        result['type'] = self.GetType(None)
        return result

    #GetPHPV
    def GetPv(self,versions,update):
        versions = versions.split(',')
        update = update.split(',')
        updates = []
        for up in update:
            if up[:3] in versions: updates.append(up)
        return ','.join(updates)

    #保存插件排序
    def savePluginSort(self,get):
        ssort = get.ssort.split('|')
        data = self.GetList(None)
        l = len(data)
        for i in range(len(ssort)):
            if int(ssort[i]) > 1000: continue
            for n in range(l):
                if data[n]['pid'] == int(ssort[i]): data[n]['sort'] = i
        public.writeFile(self.__list,json.dumps(data))
        return public.return_msg_gettext(True, public.lang("Sort saved"))

    #检查是否安装
    def checksSetup(self,name,checks,vers = ''):
        tmp = checks.split(',')
        versions = []
        path = '/www/server/' + name + '/version.pl'
        v1 = ''
        if os.path.exists(path): v1 = public.xss_version(public.readFile(path).strip())
        if name == 'nginx': v1 = v1.replace('1.10', '1.12')
        if not self.__tasks:
            self.__tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        isStatus = 0
        versArr = vers.split(',')
        for v in versArr:
            version = {}

            v2 = v
            if name == 'php': v2 = v2.replace('.','')
            status = False
            for tm in tmp:
                if name == 'php':
                    path = '/www/server/php/' + v2
                    if os.path.exists(path + '/bin/php') and not os.path.exists(path + '/version.pl'):
                        public.ExecShell("echo `"+path+"/bin/php 2>/dev/null -v|grep cli|awk '{print $2}'` > " + path + '/version.pl')
                    try:
                        v1 = public.xss_version(public.readFile(path+'/version.pl').strip())
                        if not v1: public.ExecShell('rm -f ' + path + '/version.pl')
                    except:
                        v1 = ""
                    if os.path.exists(tm.replace('VERSION',v2)): status = True
                else:
                    if os.path.exists(tm) and isStatus == 0:
                        if len(versArr) > 1:
                            im = v1.find(v)
                            if im != -1 and im < 3:
                                status = True
                                isStatus += 1
                        else:
                            status = True
                            isStatus += 1
            #处理任务标记
            if not self.__tasks:
                self.__tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
            isTask = '1'
            for task in self.__tasks:
                tmpt = public.getStrBetween('[',']',task['name'])
                if not tmpt:continue
                tmp1 = tmpt.split('-')
                name1 = tmp1[0].lower()
                if name == 'php':
                    if name1 == name and tmp1[1] == v: isTask = task['status']
                else:
                    if name1 == 'pure': name1 = 'pure-ftpd'
                    if name1 == name: isTask = task['status']

            infoFile = 'plugin/' + name + '/info.json'
            if os.path.exists(infoFile):
                try:
                    tmps = json.loads(public.readFile(infoFile))
                    if tmps: v1 = tmps['versions']
                except:pass

            if name == 'memcached':
                if os.path.exists('/etc/init.d/memcached'):
                    v1 = session.get('memcachedv')
                    if not v1:
                        v1 = public.ExecShell("memcached -V|awk '{print $2}'")[0].strip()
                        session['memcachedv'] = v1
            if name == 'apache':
                if os.path.exists('/www/server/apache/bin/httpd'):
                    v1 = session.get('httpdv')
                    if not v1:
                        v1 = public.ExecShell(r"/www/server/apache/bin/httpd -v|grep Apache|awk '{print $3}'|sed 's/Apache\///'")[0].strip();
                        session['httpdv'] = v1
            #if name == 'mysql':
            #    if os.path.exists('/www/server/mysql/bin/mysql'): v1 = public.ExecShell("mysql -V|awk '{print $5}'|sed 's/,//'")[0].strip();

            version['status'] = status
            version['version'] = v
            version['task'] = isTask
            version['no'] = v1
            versions.append(version)
        return self.checkRun(name,versions)

    #检查是否启动
    def checkRun(self,name,versions):
        if name == 'php':
            path = '/www/server/php'
            pids = psutil.pids()
            for i in range(len(versions)):
                if versions[i]['status']:
                    v4 = versions[i]['version'].replace('.','')
                    versions[i]['run'] = os.path.exists('/tmp/php-cgi-' + v4 + '.sock')
                    pid_file = path + '/' + v4 + '/var/run/php-fpm.pid'
                    versions[i]['process_id'] = public.readFile(pid_file)
                    if versions[i]['run'] and os.path.exists(pid_file):
                        if not int(public.readFile(pid_file)) in pids:
                            versions[i]['run'] = False

                    versions[i]['fpm'] = os.path.exists('/etc/init.d/php-fpm-'+v4)
                    phpConfig = self.GetPHPConfig(v4)
                    versions[i]['max'] = phpConfig['max']
                    versions[i]['maxTime'] = phpConfig['maxTime']
                    versions[i]['pathinfo'] = phpConfig['pathinfo']
                    versions[i]['display'] = os.path.exists(path + '/' + v4 + '/display.pl')
                    if len(versions) < 5: versions[i]['run'] = True

        elif name == 'nginx':
            status = False
            if os.path.exists('/etc/init.d/nginx'):
                pidf = '/www/server/nginx/logs/nginx.pid'
                if os.path.exists(pidf):
                    try:
                        pid = public.readFile(pidf)
                        pname = self.checkProcess(pid)
                        if pname: status = True
                    except:
                        status = False
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'apache':
            status = False
            if os.path.exists('/etc/init.d/httpd'):
                pidf = '/www/server/apache/logs/httpd.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    status = self.checkProcess(pid)
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'mysql':
            status = os.path.exists('/tmp/mysql.sock')
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.getPid('jsvc'): status = True
            if not status:
                if self.getPid('java'): status = True
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'pure-ftpd':
             for i in range(len(versions)):
                pidf = '/var/run/pure-ftpd.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    versions[i]['run'] = self.checkProcess(pid)
                    if not versions[i]['run']: public.ExecShell('rm -f ' + pidf)
        elif name == 'phpmyadmin':
            for i in range(len(versions)):
                if versions[i]['status']: versions[i] = self.getPHPMyAdminStatus()
        elif name == 'redis':
            for i in range(len(versions)):
                pidf = '/var/run/redis_6379.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    versions[i]['run'] = self.checkProcess(pid)
                    if not versions[i]['run']: public.ExecShell('rm -f ' + pidf)
        elif name == 'memcached':
            for i in range(len(versions)):
                pidf = '/var/run/memcached.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    versions[i]['run'] = self.checkProcess(pid)
                    if not versions[i]['run']: public.ExecShell('rm -f ' + pidf)
        else:
            for i in range(len(versions)):
                if versions[i]['status']: versions[i]['run'] = True
        return versions

    #取PHPMyAdmin状态
    def getPHPMyAdminStatus(self):
        import re
        tmp = {}
        setupPath = '/www/server'
        configFile = setupPath + '/nginx/conf/nginx.conf'
        pauth = False
        pstatus = False
        phpversion = "54"
        phpport = '888'
        ssl_port = '887'
        ssl_enabled = False
        if os.path.exists(configFile):
            conf = public.readFile(configFile)
            rep = r"listen\s+([0-9]+)\s*;"
            rtmp = re.search(rep,conf)
            if rtmp:
                phpport = rtmp.groups()[0]

            # SSL配置文件查看
            ssl_config_file = '{}/vhost/nginx/phpmyadmin.conf'.format(public.get_panel_path())
            if os.path.exists(ssl_config_file) and os.path.getsize(ssl_config_file) > 10:
                tmps = public.readFile(ssl_config_file)
                m = re.search(r"listen\s*(\d+)", tmps)
                if m is not None:
                    ssl_enabled = True
                    ssl_port = m.group(1)

            if conf.find('AUTH_START') != -1: pauth = True
            if conf.find(setupPath + '/stop') == -1: pstatus = True
            configFile = setupPath + '/nginx/conf/enable-php.conf'
            if not os.path.exists(configFile): public.writeFile(configFile,public.readFile(setupPath + '/nginx/conf/enable-php-54.conf'))
            conf = public.readFile(configFile)
            rep = r"php-cgi-([0-9]+)\.sock"
            rtmp = re.search(rep,conf)
            if rtmp:
                phpversion = rtmp.groups()[0]
            else:
                rep = r'127.0.0.1:10(\d{2,2})1'
                rtmp = re.findall(rep,conf)
                if rtmp:
                    phpversion = rtmp[0]
                else:
                    rep = r"php-cgi.*\.sock"
                    public.writeFile(configFile,conf)
                    phpversion = '54'

        configFile = setupPath + '/apache/conf/extra/httpd-vhosts.conf'
        if os.path.exists(configFile):
            conf = public.readFile(configFile)
            rep = r"php-cgi-([0-9]+)\.sock"
            rtmp = re.search(rep,conf)
            if rtmp:
                phpversion = rtmp.groups()[0]
            rep = r"Listen\s+([0-9]+)\s*\n"
            rtmp = re.search(rep,conf)
            if rtmp:
                phpport = rtmp.groups()[0]

            # SSL配置文件查看
            ssl_config_file = '{}/vhost/apache/phpmyadmin.conf'.format(public.get_panel_path())
            if os.path.exists(ssl_config_file) and os.path.getsize(ssl_config_file) > 10:
                tmps = public.readFile(ssl_config_file)
                m = re.search(r"Listen\s*(\d+)", tmps)
                if m is not None:
                    ssl_enabled = True
                    ssl_port = m.group(1)

            if conf.find('AUTH_START') != -1: pauth = True
            if conf.find('/www/server/stop') == -1: pstatus = True

        if os.path.exists('/usr/local/lsws/bin/lswsctrl'):
            result = self._get_ols_myphpadmin_info()
            if result:
                phpversion = result['php_version']
                phpport = result['php_port']
                pauth = result['pauth']
                pstatus = result['pstatus']
        try:
            vfile = setupPath + '/phpmyadmin/version.pl'
            if os.path.exists(vfile):
                tmp['version'] = public.xss_version(public.readFile(vfile).strip())
                tmp['status'] = True
                tmp['no'] = tmp['version']
            else:
                tmp['version'] = ""
                tmp['status'] = False
                tmp['no'] = ""

            tmp['run'] = pstatus
            tmp['phpversion'] = phpversion
            tmp['ssl_enabled'] = ssl_enabled
            tmp['port'] = phpport
            tmp['ssl_port'] = ssl_port
            tmp['auth'] = pauth
        except Exception as ex:
            tmp['status'] = False
            tmp['error'] = str(ex)
        return tmp

    def _get_ols_myphpadmin_info(self):
        filename = "/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        conf = public.readFile(filename)
        if not conf:return False
        reg = r'/usr/local/lsws/lsphp(\d+)/bin/lsphp'
        php_v = re.search(reg,conf)
        phpversion = '73'
        phpport = '888'
        if php_v:
            phpversion = php_v.group(1)
        filename = '/www/server/panel/vhost/openlitespeed/listen/888.conf'
        conf = public.readFile(filename)
        reg = r'address\s+\*\:(\d+)'
        php_port = re.search(reg,conf)
        if php_port:
            phpport = php_port.group(1)
        pauth = False
        pstatus = False
        if conf.find('/www/server/stop') == -1: pstatus = True
        return {'php_version':phpversion,'php_port':phpport,'pauth':pauth,'pstatus':pstatus}

    #取PHP配置
    def GetPHPConfig(self,version):
        import re
        setupPath = '/www/server'
        file = setupPath + "/php/"+version+"/etc/php.ini"
        phpini = public.readFile(file)
        file = setupPath + "/php/"+version+"/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = r"upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep,phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep,phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0

        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep,phpini).groups()

            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False

        return data

    #名取PID
    def getPid(self,pname):
        try:
            if not self.pids: self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True
            return False
        except: return True

    #检测指定进程是否存活
    def checkProcess(self,pid):
        try:
            if not self.pids: self.pids = psutil.pids()
            if int(pid) in self.pids: return True
            return False
        except: return False

    #获取配置模板
    def getConfigHtml(self,get):
        filename = self.__install_path + '/' + get.name + '/index.html'
        if not os.path.exists(filename): return public.return_msg_gettext(False, public.lang("This plugin does NOT have template!"))
        mimetype = 'text/html'
        cache_time = 0 if public.is_debug() else 86400
        self.plugin_open_total(get.name)
        import flask
        if flask.__version__ < "2.1.0":
            return send_file(filename,
                        mimetype = mimetype,
                        as_attachment = True,
                        add_etags = True,
                        conditional = True,
                        cache_timeout = cache_time)
        else:
            return send_file(filename,
                        mimetype = mimetype,
                        as_attachment = True,
                        etag = True,
                        conditional = True,
                        max_age = cache_time)


    def creatab_open_total_table(self,sql):
        '''
            @name 创建插件打开统计表
            @author hwliang<2021-06-26>
            @param sql<db.Sql> 数据库对像
            @return void
        '''
        if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'open_total')).count():
            csql = '''CREATE TABLE IF NOT EXISTS `open_total` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`plugin_name` REAL,
`num` INTEGER
)'''
            sql.execute(csql,())


    def plugin_open_total(self,plugin_name):
        '''
            @name 插件打开统计
            @author hwliang<2021-06-26>
            @param plugin_name<string> 插件名称
            @return void
        '''
        import db
        sql = db.Sql().dbfile('plugin_total')
        self.creatab_open_total_table(sql)
        pdata = {
            "plugin_name":plugin_name,
            "num":1
            }

        num = sql.table('open_total').where('plugin_name=?',plugin_name).getField('num')
        if not num:
            sql.table('open_total').insert(pdata)
        else:
            sql.table('open_total').where('plugin_name=?',plugin_name).setField('num',num+1)

    def get_usually_plugin(self,get):
        '''
            @name 获取常用插件
            @author hwliang<2021-06-26>
            @param get<obj_dict>
            @return list
        '''
        import db
        sql = db.Sql().dbfile('plugin_total')
        self.creatab_open_total_table(sql)
        plugin_list =  sql.table('open_total').order('num desc').limit(10).select()
        usually_list = []
        for p in plugin_list:
            plugin_info = self.get_soft_find(p['plugin_name'])
            if plugin_info:
                if plugin_info['setup']:
                    usually_list.append(plugin_info)
            if len(usually_list) >= 5: break
        return usually_list


    def get_plugin_upgrades(self,get):
        '''
            @name 获取指定插件的近期更新历史
            @author hwliang<2021-06-30>
            @param get<obj_dict>{
                plugin_name: string 插件名称
            }
            @return list
        '''
        plugin_name = get.plugin_name
        if getattr(get,'show',0):
            plugin_info = self.__get_plugin_find(plugin_name)
            if plugin_info and 'versions' in plugin_info:
                return plugin_info['versions']
            return []
        else:
            return self.__get_plugin_upgrades(plugin_name)

    #取插件信息
    def getPluginInfo(self,get):
        try:
            pluginInfo = self.GetFind(get.name)
            apacheVersion = ""
            try:
                apavFile = '/www/server/apache/version.pl'
                if os.path.exists(apavFile):
                    apacheVersion = public.xss_version(public.readFile(apavFile).strip())
            except:
                pass
            if pluginInfo['name'] == 'php':
                if apacheVersion == '2.2':
                    pluginInfo['versions'] = '5.2,5.3,5.4'
                elif apacheVersion == '2.4':
                    pluginInfo['versions'] = '5.3,5.4,5.5,5.6,7.0,7.1,7.2,7.3,7.4'

            pluginInfo['versions'] = self.checksSetup(pluginInfo['name'],pluginInfo['checks'],pluginInfo['versions'])
            if get.name == 'php':
                pluginInfo['phpSort'] = public.readFile('/www/server/php/sort.pl')
            return pluginInfo
        except:
            return False

    #取插件状态
    def getPluginStatus(self,get):
        find = self.GetFind(get.name)
        versions = []
        path = '/www/server/php'
        for version in find['versions'].split(','):
            tmp = {}
            tmp['version'] = version
            if get.name == 'php':
                tmp['status'] = os.path.exists(path + '/' + version.replace(',','') + '/display.pl')
            else:
                tmp['status'] = find['status']
            versions.append(tmp)
        return versions

    #设置插件状态
    def setPluginStatus(self,get):
        if get.name == 'php':
            isRemove = True
            path = '/www/server/php'
            if get.status == '0':
                versions = self.GetFind(get.name)['versions']
                public.ExecShell('rm -f ' + path + '/' + get.version.replace('.','') + '/display.pl')
                for version in versions.split(','):
                    if os.path.exists(path + '/' + version.replace('.','') + '/display.pl'):
                        isRemove = False
                        break
            else:
                public.writeFile(path + '/' + get.version.replace('.','') + '/display.pl','True')

            if isRemove:
                self.SetField(get.name, 'display', int(get.status))
        else:
            self.SetField(get.name, 'display', int(get.status))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    #从云端获取插件列表
    def getCloudPlugin(self,get):
        if session.get('getCloudPlugin') and get != None: return public.return_msg_gettext(True,'Your plugin list is already the latest version {}!',("-1",))
        import json
        if not session.get('download_url'): session['download_url'] = 'http://node.iPanel.com'

        #获取列表
        try:
            newUrl = public.get_url()
            if os.path.exists('plugin/beta/config.conf'):
                download_url = newUrl + '/install/list.json'
            else:
                download_url = newUrl + '/install/list_pro.json'
            data = json.loads(public.httpGet(download_url))
            session['download_url'] = newUrl
        except:
            download_url = session['download_url'] + '/install/list_pro.json'
            data = json.loads(public.httpGet(download_url))

        n = i = j = 0

        lists = self.GetList(None)

        for i in range(len(data)):
            for pinfo in lists:
                if data[i]['name'] != pinfo['name']: continue
                data[i]['display'] = pinfo['display']
            if data[i]['default']:
                get.name = data[i]['name']
                self.install(get)

        public.writeFile(self.__list,json.dumps(data))

        #获取分类
        try:
            download_url = session['download_url'] + '/install/type.json'
            types = json.loads(public.httpGet(download_url))
            public.writeFile(self.__type,json.dumps(types))
        except:
            pass

        self.getCloudPHPExt(get)
        self.GetCloudWarning(get)
        session['getCloudPlugin'] = True
        return public.return_msg_gettext(True, public.lang("Software list updated!"))

    #刷新缓存
    def flush_cache(self,get):
        self.getCloudPlugin(None)
        return public.return_msg_gettext(True, public.lang("Software list updated!"))

    #获取PHP扩展
    def getCloudPHPExt(self,get=None):
        import json
        try:
            key = 'php_ext_cache'
            if cache.get(key): return 1
            surl = public.get_url()
            download_url = surl + '/install/lib/phplib.json'
            tstr = public.httpGet(download_url)
            data = json.loads(tstr)
            if not data: return 2
            public.writeFile('data/phplib.conf',json.dumps(data))

            # download_url = surl + '/license/md5.txt'
            # li_md5 = public.httpGet(download_url)
            # if not li_md5: return 3
            # li_md5 = li_md5.strip()
            # if len(li_md5) != 32: return 4
            # l_file = 'BTPanel/templates/default/license.html'
            # lfile2 = 'data/license.md5'
            # old_md5 = ''
            # if os.path.exists(lfile2):
            #     old_md5 = public.readFile(lfile2)

            # if li_md5 != old_md5:
            #     download_url = surl + '/license/license.html'
            #     public.downloadFile(download_url,l_file)
            #     old_md5 = public.FileMd5(l_file)
            #     if li_md5 == old_md5:
            #         public.writeFile(lfile2,old_md5)
            #         s_file = 'data/licenes.pl'
            #         if os.path.exists(s_file):
            #             os.remove(s_file)
            cache.set(key,86400)
            return True
        except:
            return public.get_error_info()



    #获取警告列表
    def GetCloudWarning(self,get):
        import json
        if not session.get('download_url'): session['download_url'] = public.get_url()
        download_url = session['download_url'] + '/install/warning.json'
        tstr = public.httpGet(download_url)
        data = json.loads(tstr)
        if not data: return False
        wfile = 'data/warning.json'
        wlist = json.loads(public.readFile(wfile))
        for i in range(len(data['data'])):
            for w in wlist['data']:
                if data['data'][i]['name'] != w['name']: continue
                data['data'][i]['ignore_count'] = w['ignore_count']
                data['data'][i]['ignore_time'] = w['ignore_time']
        public.writeFile(wfile,json.dumps(data))
        return data

    #名取标题
    def get_title_byname(self,get):
        get.sName = get.name
        find = self.get_soft_find(get)
        return find['title']


    def a(self, get):
        try:
            return public.run_plugin(get.name, get.s, get)
        except:
            return public.get_error_object(None, plugin_name=get.name)

    #上传插件包
    def update_zip(self,get = None,tmp_file = None, update = False):
        tmp_path = '/www/server/panel/temp'
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path,mode=384)

        if tmp_file:
            if not os.path.exists(tmp_file): return public.return_msg_gettext(False, public.lang("File download failed!"))


        if get:
            public.ExecShell("rm -rf " + tmp_path + '/*')
            tmp_file = tmp_path + '/plugin_tmp.zip'
            from werkzeug.utils import secure_filename
            from flask import request
            f = request.files['plugin_zip']
            if f.filename[-4:] != '.zip': tmp_file = tmp_path + '/plugin_tmp.tar.gz'

            f.save(tmp_file)


        import panelTask
        panelTask.bt_task()._unzip(tmp_file,tmp_path,'','/dev/null')
        os.remove(tmp_file)
        p_info = tmp_path + '/info.json'
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(tmp_path):
                if len(df[2]) < 3: continue
                if not 'info.json' in df[2]: continue
                if not 'install.sh' in df[2]: continue
                if not os.path.exists(df[0] + '/info.json'): continue
                d_path = df[0]
            if d_path:
                tmp_path = d_path
                p_info = tmp_path + '/info.json'
        try:
            try:
                data = json.loads(public.ReadFile(p_info))
            except:
                data = json.loads(public.ReadFile(p_info).decode('utf-8-sig'))
            data['size'] = public.get_path_size(tmp_path)
            if not 'author' in data: data['author'] = public.lang("Unknown")
            if not 'home' in data: data['home'] = 'https://www.hypr.local/bbs/forum-40-1.html'

            plugin_path = '/www/server/panel/plugin/' + data['name'] + '/info.json'
            data['old_version'] = '0'
            data['tmp_path'] = tmp_path
            if os.path.exists(plugin_path):
                try:
                    old_info = json.loads(public.ReadFile(plugin_path))
                    data['old_version'] = old_info['versions']
                except:pass
        except:
            public.ExecShell("rm -rf " + tmp_path + '/*')
            return public.return_msg_gettext(False, public.lang("No plugin info found in the archive, please check the plugin package!"))

        data['update'] = update
        return data

    #导入插件包
    def input_zip(self,get):
        if not os.path.exists(get.tmp_path): return public.return_msg_gettext(False, public.lang("Temporary file does NOT exist, please re-upload!"))
        plugin_path = '/www/server/panel/plugin/' + get.plugin_name
        if not os.path.exists(plugin_path): os.makedirs(plugin_path)
        public.ExecShell(r"\cp -a -r " + get.tmp_path + '/* ' + plugin_path + '/')
        public.ExecShell('chmod -R 600 ' + plugin_path)
        self.set_pyenv(plugin_path + '/install.sh')
        public.ExecShell('cd ' + plugin_path + ' && bash install.sh install &> /tmp/panelShell.pl')
        p_info = public.ReadFile(plugin_path + '/info.json')
        public.ExecShell("rm -rf /www/server/panel/temp/*")
        if p_info:
            #----- 增加图标复制 hwliang<2021-03-23> -----#
            icon_sfile = plugin_path + '/icon.png'
            icon_dfile = '/www/server/panel/BTPanel/static/img/soft_ico/ico-{}.png'.format(get.plugin_name)
            if os.path.exists(plugin_path + '/icon.png'):
                import shutil
                shutil.copyfile(icon_sfile,icon_dfile)
            #----- 增加图标复制 END -----#
            public.write_log_gettext('Software manager','Installed third-party plugin [{}]' ,(json.loads(p_info)['title'],))
            return public.return_msg_gettext(True, public.lang("Installation succeeded!"))
        public.ExecShell("rm -rf " + plugin_path)
        return public.return_msg_gettext(False, public.lang("Installation failed"))


    #导出插件包
    def export_zip(self,get):
        plugin_path = '/www/server/panel/plugin/' + get.plugin_name
        if not os.path.exists(plugin_path): return public.return_msg_gettext(False, public.lang("The specified plugin does not exist!"))

        get.sfile = plugin_path + '/'
        get.dfile = '/www/server/panel/temp/bt_plugin_' + get.plugin_name + '.zip'
        get.type = 'zip'
        import files
        files.files().Zip(get)
        if not os.path.exists(get.dfile): return public.return_msg_gettext(False, public.lang("Export failed, please check permissions!"))
        return public.return_msg_gettext(True,get.dfile)


    #获取编译参数
    def get_make_args(self,get):
        config_path = 'install/' + get.name
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        #读支持的编译参数列表
        make_args = []
        for p_name in os.listdir(config_path):
            path = os.path.join(config_path,p_name)
            if not os.path.isdir(path): continue
            make_info = {"name":p_name,"init":"","args":"","ps":""}
            init_file = os.path.join(path,'init.sh')
            args_file = os.path.join(path,'args.pl')
            ps_file = os.path.join(path,'ps.pl')
            if not os.path.exists(args_file):
                continue
            if os.path.exists(init_file):
                make_info['init'] = public.readFile(init_file)
            if os.path.exists(ps_file):
                make_info['ps'] = public.readFile(ps_file)
            make_info['args'] = public.readFile(args_file)
            make_args.append(make_info)
        #读当前配置
        data = {'args':make_args,'config':''}
        config_file = config_path + '/config.pl'
        if os.path.exists(config_file):
            data['config'] = public.readFile(config_file)
        return data

    #添加编译参数
    def add_make_args(self,get):
        get.args_name = get.args_name.strip()
        get.name = get.name.strip()
        get.ps = get.ps.strip()
        if not re.match(r'^\w+$',get.args_name):
            return public.return_msg_gettext(False, public.lang("Non-compliant names can only be numbers, letters, underscores"))

        config_path = os.path.join('install' , get.name , get.args_name)
        if not os.path.exists(config_path):
            os.makedirs(config_path,384)

        init_file = os.path.join(config_path,'init.sh')
        args_file = os.path.join(config_path,'args.pl')
        ps_file = os.path.join(config_path,'ps.pl')
        public.writeFile(init_file,get.init.replace("\r\n","\n"))
        public.writeFile(args_file,get.args)
        public.writeFile(ps_file,get.ps)

        public.write_log_gettext('Software manager','Add custom compilation parameters: {}:{}',(get.name,get.args_name))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    #删除编译参数
    def del_make_args(self,get):
        get.args_name = get.args_name.strip()
        get.name = get.name.strip()
        if not re.match(r'^\w+$',get.args_name):
            return public.return_msg_gettext(False, public.lang("Non-compliant names can only be numbers, letters, underscores"))
        config_path = os.path.join('install' , get.name , get.args_name)
        if not os.path.exists(config_path):
            return public.return_msg_gettext(False, public.lang("The specified custom compilation parameters do not exist!"))
        public.ExecShell("rm -rf {}".format(config_path))
        config_file = 'install/' + get.name + '/config.pl'
        if os.path.exists(config_file):
            config_data = public.readFile(config_file).split("\n")
            if get.args_name in config_data:
                config_data.remove(get.args_name)
                public.writeFile(config_file,"\n".join(config_data))
        public.write_log_gettext('Software manager','Remove custom compilation parameters: {}:{}',(get.name,get.args_name))
        return public.return_msg_gettext(True, public.lang("Successfully deleted"))


    #设置当前编译参数
    def set_make_args(self,get):
        get.args_names = get.args_names.strip().split("\n")
        get.name = get.name.strip()
        config_file = 'install/' + get.name + '/config.pl'
        config_data = []
        for args_name in get.args_names:
            path = 'install/' + get.name + '/' + args_name
            if not os.path.exists(path): continue
            if args_name in config_data: continue
            config_data.append(args_name)
        public.writeFile(config_file,"\n".join(config_data))
        public.write_log_gettext('Software manager','Setup software: Custom compilation parameters for {} are configured as: {}'.format(get.name,config_data))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    # 安装插件
    def __install_plugin(self, upgrade_plugin_name, upgrade_version=None):
        '''
            @name 安装指定插件
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @param upgrade_version<string> 插件版本 版本号.指定版本号 / tls.最新正式版 / beta.最新测试版
            @return dict
        '''
        self.__plugin_name = upgrade_plugin_name
        plugin_info = self.__get_plugin_find(upgrade_plugin_name)
        if not plugin_info:
            raise public.PanelError('Plugin not found')
        if not plugin_info['versions']:
            raise public.PanelError('Not available versions for this plugin')
        if not upgrade_version:
            upgrade_version = '{}.{}'.format(
                plugin_info['versions'][0]['m_version'],
                plugin_info['versions'][0]['version'])
        filename = self.__download_plugin(upgrade_plugin_name, upgrade_version)
        # 如果下载失败
        if isinstance(filename, dict):
            return filename
        return self.__unpackup_plugin(filename)

    # 修复插件
    def __repair_plugin(self, upgrade_plugin_name, upgrade_version=None):
        '''
            @name 修复指定插件
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @param upgrade_version<string> 插件版本 版本号.指定版本号 / tls.最新正式版 / beta.最新测试版
            @return dict
        '''
        self.__install_opt = 'r'
        return self.__install_plugin(upgrade_plugin_name, upgrade_version)

    # 升级插件版本
    def __upgrade_plugin(self, upgrade_plugin_name, upgrade_version=None):
        '''
            @name 升级到指定版本
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @param upgrade_version<string> 插件版本 版本号.指定版本号 / tls.最新正式版 / beta.最新测试版
            @return dict
        '''
        self.__install_opt = 'u'
        return self.__install_plugin(upgrade_plugin_name, upgrade_version)

    # 获取插件信息
    def __get_plugin_info(self, upgrade_plugin_name):
        '''
            @name 获取插件信息
            @author hwliang<2021-06-15>
            @param upgrade_plugin_name<string> 插件名称
            @return dict
        '''
        plugin_info_file = '{}/{}/info.json'.format(self.__plugin_path,
                                                    upgrade_plugin_name)
        if not os.path.exists(plugin_info_file): return {}
        info_body = self.__read_file(plugin_info_file)
        if not info_body: return {}
        plugin_info = json.loads(info_body)
        return plugin_info

    # 获取插件最近1条更新日志
    def __get_update_msg(self, upgrade_plugin_name, upgrade_version):
        '''
            @name 检查指定插件版本更新日志
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @param upgrade_version<string> 插件版本
            @return string
        '''
        plugin_update_msg = ''
        plugin_info = self.__get_plugin_find(upgrade_plugin_name)
        if not plugin_info: return plugin_update_msg
        for _version_info in plugin_info['versions']:
            l_version = '{}.{}'.format(_version_info['m_version'],
                                       _version_info['version'])
            if l_version == upgrade_version:
                plugin_update_msg = _version_info['update_msg']
                break
        return plugin_update_msg

    # 获取插件最近10条更新日志
    def __get_plugin_upgrades(self, upgrade_plugin_name):
        '''
            @name 检查指定插件最近10条更新日志
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @return list
        '''
        plugin_info = self.__get_plugin_find(upgrade_plugin_name)
        if not plugin_info: return []

        try:
            upgrade_list = public.httpPost(
                self.__api_root_url + '/down/get_update_msg',
                {'soft_id': plugin_info['id']})
            return json.loads(upgrade_list)
        except:
            return []

    # 获取指定软件信息
    def __get_plugin_find(self, upgrade_plugin_name=None):
        '''
            @name 获取指定软件信息
            @author hwliang<2021-06-15>
            @param upgrade_plugin_name<string> 插件名称
            @return dict
        '''
        self.__ensure_plugin_list_obtained(True)

        for p_data_info in self.__plugin_list['list']:
            if p_data_info['name'] == upgrade_plugin_name:
                upgrade_plugin_name = p_data_info['name']
                return p_data_info

        # 如果不在插件列表中
        return self.__get_plugin_info(upgrade_plugin_name)

    # 检查插件依赖
    def __check_dependent(self, upgrade_plugin_name):
        '''
            @name 检查指定插件的依赖安装情况
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @return dict
        '''
        plugin_info = self.__get_plugin_find(upgrade_plugin_name)
        if not plugin_info: return {}
        if not plugin_info['dependent']: return {}
        deployment_list = {}
        for dependent_plu_name in plugin_info['dependent'].split(','):
            p_info = self.__get_plugin_find(dependent_plu_name)
            if not p_info: continue
            deployment_list[dependent_plu_name] = os.path.exists(
                p_info['install_checks'])
        return deployment_list

    # 读取指定文件
    def __read_file(self, filename, open_mode='r'):
        '''
            @name 读取指定文件
            @author hwliang<2021-06-16>
            @param filename<string> 文件名
            @param mode<string> 打开模式, 默认: r
            @return bytes or string
        '''
        f_object = open(filename, mode=open_mode)
        file_body = f_object.read()
        f_object.close()
        return file_body

    # 解包插件压缩包
    def __unpackup_plugin(self, tmp_file):
        '''
            @name 解包插件包
            @author hwliang<2021-06-21>
            @param tmp_file<string> 下载好的保存路径，从self.download_plugin方法中获取
            @return dict
        '''
        if type(tmp_file) == dict:
            return tmp_file

        if "false" in tmp_file or "错误" in tmp_file:
            return json.loads(tmp_file)

        s_tmp_path = self.__tmp_path
        if not os.path.exists(s_tmp_path):
            os.makedirs(s_tmp_path, mode=384)

        if tmp_file:
            if not os.path.exists(tmp_file):
                return public.returnMsg(False, public.lang("File download failed!"))
            import panelTask as plu_panelTask
            plu_panelTask.bt_task()._unzip(tmp_file, s_tmp_path, '',
                                           '/dev/null')
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

        s_tmp_path = os.path.join(s_tmp_path, self.__plugin_name)

        p_info = os.path.join(s_tmp_path, 'info.json')
        if not os.path.exists(p_info):
            d_path = None
            for plugin_df in os.walk(s_tmp_path):
                if len(plugin_df[2]) < 3: continue
                if not 'info.json' in plugin_df[2]: continue
                if not 'install.sh' in plugin_df[2]: continue
                if not os.path.exists(plugin_df[0] + '/info.json'): continue
                d_path = plugin_df[0]
            if d_path:
                s_tmp_path = d_path
                p_info = s_tmp_path + '/info.json'
        try:
            try:
                plugin_data_info = json.loads(public.ReadFile(p_info))
            except:
                plugin_data_info = json.loads(self.__read_file(p_info))

            plugin_data_info['size'] = public.get_path_size(s_tmp_path)
            if not 'author' in plugin_data_info:
                plugin_data_info['author'] = 'iPanel'
            if not 'home' in plugin_data_info:
                plugin_data_info['home'] = '{}'.format(public.OfficialApiBase())

            p_info_file = self.__plugin_path + plugin_data_info[
                'name'] + '/info.json'
            plugin_data_info['old_version'] = '0'
            plugin_data_info['tmp_path'] = s_tmp_path
            if os.path.exists(p_info_file):
                try:
                    old_info = json.loads(public.ReadFile(p_info_file))
                    plugin_data_info['old_version'] = old_info['versions']
                except:
                    pass
        except:
            public.ExecShell("rm -rf " + s_tmp_path + '/*')
            return public.get_error_object(plugin_name=self.__plugin_name)
        plugin_data_info['install_opt'] = self.__install_opt
        plugin_data_info['dependent'] = self.__check_dependent(plugin_data_info['name'])
        plugin_data_info['update_msg'] = self.__get_update_msg(
            plugin_data_info['name'], plugin_data_info['versions'])
        not_check = self.not_cpu_or_bit(plugin_data_info)
        if not_check:
            if os.path.exists(s_tmp_path): shutil.rmtree(s_tmp_path)
            return not_check

        return plugin_data_info

    # 检测是否为不支持的平台和系统位数
    def not_cpu_or_bit(self, plugin_data_info):
        '''
            @name 检测是否为不支持的平台和系统位数
            @author hwliang<2021-07-07>
            @param plugin_data_info<dict> 插件信息数据
            @return dict or None
        '''
        if 'not_os_bit' in plugin_data_info:
            if public.get_sysbit() == int(plugin_data_info['not_os_bit']):
                return public.returnMsg(
                    False,
                    'Not supported for {}bit systems.'.format(plugin_data_info['not_os_bit']))
        if 'not_cpu_type' in plugin_data_info:
            if not plugin_data_info['not_cpu_type']: return None
            machine = os.uname().machine
            for c_type in plugin_data_info['not_cpu_type']:
                c_type = c_type.lower()
                result = public.returnMsg(
                    False, 'Not supported for {},{}'.format(c_type, machine))
                if c_type in ['arm', 'aarch64', 'aarch']:
                    if machine in ['aarch64', 'aarch']:
                        return result
                elif c_type in ['mips', 'mips64', 'mips64el']:
                    if machine.find('mips') != -1:
                        return result
                elif c_type in ['x86', 'x86-64']:
                    if machine in ['x86', 'x86-64']:
                        return result
        return None

    # 下载插件安装包
    def __download_plugin(self, upgrade_plugin_name, upgrade_version):
        '''
            @name 下载插件包
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @param upgrade_version<string> 插件版本
            @return string 保存路径
        '''

        pkey = '{}_pre'.format(upgrade_plugin_name)
        pdata = public.get_user_info()
        pdata['name'] = upgrade_plugin_name
        pdata['version'] = upgrade_version
        pdata['os'] = 'Linux'
        pdata['environment_info'] = json.dumps(public.fetch_env_info(), ensure_ascii=False)
        filename = '{}/{}.zip'.format(self.__tmp_path, upgrade_plugin_name)
        if not os.path.exists(self.__tmp_path):
            os.makedirs(self.__tmp_path, 384)

        if not cache.get(pkey):
            import config, socket
            import requests.packages.urllib3.util.connection as urllib3_conn
            _ip_type = config.config().get_request_iptype()
            old_family = urllib3_conn.allowed_gai_family
            if _ip_type == 'ipv4':
                urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
            elif _ip_type == 'ipv6':
                urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6
            try:
                download_res = requests.post(
                    self.__download_url,
                    pdata,
                    headers=public.get_requests_headers(),
                    timeout=(60, 1800),
                    stream=True)
            except Exception as ex:
                str_ex = str(ex)
                if 'Name or service not known' in str_ex:
                    return public.returnMsg(False,
                                            public.lang('Error: Name or service not known'))
                elif 'Failed to establish a new connection' in str_ex:
                    return public.returnMsg(False,
                                            public.lang('Error: Failed to establish a new connection'))
                elif 'Read timed out' in str_ex:
                    return public.returnMsg(False,
                                            public.lang('Error: Read timed out'))
                elif 'Connection refused' in str_ex:
                    return public.returnMsg(False,
                                            public.lang('Error: Connection refused'))
                elif 'Remote end closed connection without response' in str_ex:
                    return public.returnMsg(False,
                                            public.lang('Error: Remote end closed connection without response'))
                else:
                    return public.returnMsg(False, public.lang('Error: {}',str_ex))
            finally:
                urllib3_conn.allowed_gai_family = old_family

            try:
                headers_total_size = int(download_res.headers['File-size'])
            except:
                try:
                    return json.loads(download_res.text).json()
                except:
                    if download_res.text.find('<html>') != -1:
                        raise public.PanelError(
                            public.error_conn_cloud(download_res.text))
                    raise public.PanelError(download_res.text)

            res_down_size = 0
            res_chunk_size = 8192
            last_time = time.time()
            with open(filename, 'wb+') as with_res_f:
                try:
                    for download_chunk in download_res.iter_content(
                            chunk_size=res_chunk_size):
                        if download_chunk:
                            with_res_f.write(download_chunk)
                            speed_last_size = len(download_chunk)
                            res_down_size += speed_last_size
                            res_start_time = time.time()
                            res_timeout = (res_start_time - last_time)
                            res_sec_speed = int(res_down_size / res_timeout)
                            pre_text = '{}/{}/{}'.format(res_down_size,
                                                         headers_total_size,
                                                         res_sec_speed)
                            cache.set(pkey, pre_text, 3600)

                except Exception as ex:
                    ex_str = str(ex)
                    if "Read timed out" in ex_str:
                        return public.returnMsg(False, public.lang('Download timeout: {}',ex_str))
                    if "No space left on device" in ex_str:
                        return public.returnMsg(False, public.lang('No available disk space.'))
                finally:
                    with_res_f.close()
            if cache.get(pkey): cache.delete(pkey)

            if public.FileMd5(filename) != download_res.headers['Content-md5']:
                return public.returnMsg(False,  public.lang('Verify package checksum failed.'))
        else:
            while True:
                time.sleep(1)
                if not cache.get(pkey): break
            return ''
        return filename

    # 获取插件安装包下载进度
    def __get_download_speed(self, upgrade_plugin_name):
        '''
            @name 取插件下载进度
            @author hwliang<2021-06-21>
            @param upgrade_plugin_name<string> 插件名称
            @return dict
        '''
        pkey = '{}_pre'.format(upgrade_plugin_name)
        pre_text = cache.get(pkey)
        if not pre_text:
            return public.returnMsg(False, public.lang('Cannot get progress bar for this plugin.'))
        result = {"status": True}
        pre_tmp = pre_text.split('/')
        result['down_size'], result['total_size'] = (int(pre_tmp[0]),
                                                     int(pre_tmp[1]))
        result['down_pre'] = round(
            result['down_size'] / result['total_size'] * 100, 1)
        result['sec_speed'] = int(float(pre_tmp[2]))
        result['need_time'] = int(
            (result['total_size'] - result['down_size']) / result['sec_speed'])
        return result


    # 获取插件与授权信息
    def __ensure_plugin_list_obtained(self, force: bool = False):
        if force or not self.__plugin_list:
            self.__plugin_list = public.load_soft_list(force)


