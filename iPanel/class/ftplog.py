#coding: utf-8
#  + -------------------------------------------------------------------
# | iPanel
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 iPanel(www.iPanel.com) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: hezhihong <272267659@@qq.cn>
#  + -------------------------------------------------------------------
import public, os, time
try:
    from BTPanel import session
except:
    pass
#英文转月份缩写
month_list = {
    "Jan": "1",
    "Feb": "2",
    "Mar": "3",
    "Apr": "4",
    "May": "5",
    "Jun": "6",
    "Jul": "7",
    "Aug": "8",
    "Sept": "9",
    "Sep": "9",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12"
}


class ftplog:
    __AUTH_MSG =public.to_string ([84 ,104 ,105 ,115 ,32 ,102 ,101 ,97 ,116 ,117 ,114 ,101 ,32 ,105 ,115 ,32 ,101 ,120 ,99 ,108 ,117 ,115 ,105 ,118 ,101 ,32 ,116 ,111 ,32 ,116 ,104 ,101 ,32 ,112 ,114 ,111 ,32 ,101 ,100 ,105 ,116 ,105 ,111 ,110 ,44 ,32 ,112 ,108 ,101 ,97 ,115 ,101 ,32 ,97 ,99 ,116 ,105 ,118 ,97 ,116 ,101 ,32 ,105 ,116 ,32 ,102 ,105 ,114 ,115 ,116 ])

    def __init__(self):
        self.__messages_file = "/var/log/"
        self.__ftp_backup_path = public.get_backup_path() + '/pure-ftpd/'
        if not os.path.isdir(self.__ftp_backup_path):
            public.ExecShell('mkdir -p {}'.format(self.__ftp_backup_path))
        self.__script_py = public.get_panel_path() + '/script/ftplogs_cut.py'

    def get_file_list(self, path, is_bakcup=False):
        """
        @name 取所有messages日志文件
        @param path: 日志文件路径
        @return: 返回日志文件列表
        """
        files = os.listdir(path)
        if is_bakcup:
            file_name_list = [{
                "file": "/var/log/pure-ftpd.log",
                "time": int(time.time())
            }]
        else:
            file_name_list = []
        for i in files:
            tmp_dict = {}
            if not i: continue
            file_path = path + i
            tmp_dict['file'] = file_path
            if is_bakcup:
                if os.path.isfile(file_path) and i.find('pure-ftpd.log') != -1:
                    tmp_dict['time'] = int(
                        public.to_date(
                            times=os.path.basename(file_path).split('_')[0] +
                            ' 00:00:00'))
                    file_name_list.append(tmp_dict)
            else:
                if os.path.isfile(file_path) and i.find('messages') != -1:
                    tmp_dict['time'] = int(
                        public.to_date(
                            times=os.path.basename(file_path).split('-')[1] +
                            ' 00:00:00'))
                    file_name_list.append(tmp_dict)
        file_name_list = sorted(file_name_list,
                                key=lambda x: x['time'],
                                reverse=False)
        return file_name_list

    def __check_auth(self):
        from plugin_auth_v2 import Plugin as Plugin
        plugin_obj = Plugin(False)
        plugin_list = plugin_obj.get_plugin_list()
        import PluginLoader
        self.__IS_PRO_MEMBER = PluginLoader.get_auth_state() > 0
        return int(plugin_list["pro"]) > time.time() or self.__IS_PRO_MEMBER

    def set_ftp_log(self, get):
        """
        @name 开启、关闭、获取日志状态
        @author hezhihong
        @param get.exec_name 执行的动作
        """
        if not self.__check_auth():
            return public.returnMsg(False, self.__AUTH_MSG)
        if not hasattr(get, 'exec_name'):
            return public.returnMsg(False, public.lang("The parameter is incorrect！"))
        ftp_file='/etc/rsyslog.d/pure-ftpd.conf'
        write_string = '\nftp.*\t\t-/var/log/pure-ftpd.log\n'
        #获取日志状态
        if get.exec_name == 'getlog':
            if os.path.exists(ftp_file):
                return public.returnMsg(True, public.lang("start"))
            else:
                return public.returnMsg(True, public.lang("stop"))
            
        # 开启日志审计
        elif get.exec_name == 'start':
            public.writeFile(ftp_file, write_string)
            self.add_crontab()
        # 关闭日志审计
        elif get.exec_name == 'stop':
            if os.path.exists(ftp_file):
                os.remove(ftp_file)
                if os.path.exists(ftp_file):
                    return public.returnMsg(False, public.lang("failed to close the log"))
            self.del_crontab()
        public.ExecShell('systemctl restart rsyslog')
        return public.returnMsg(True, public.lang("successfully set"))

    def get_format_time(self, englist_time):
        """
        @name 时间英文转换
        """
        chinanese_time = ''
        try:
            for i in month_list.keys():
                if i in englist_time:
                    tmp_time = englist_time.replace(i, month_list[i])
                    tmp_time = tmp_time.split()
                    chinanese_time = '{}-{} {}'.format(tmp_time[0], tmp_time[1],
                                                       tmp_time[2])
                    break
            return chinanese_time
        except:
            return chinanese_time

    def get_login_log(self, get):
        """
        @name 取登录日志
        @author hezhihong
        @param get.user_name ftp用户名
        return 
        """

        search_str = 'pure-ftpd:'
        search_str2 = 'pure-ftpd['
        if not hasattr(get, 'user_name'):
            return public.returnMsg(False, public.lang("The parameter is incorrect！"))
        args = public.dict_obj()
        args.exec_name = 'getlog'
        file_name = self.__ftp_backup_path
        is_backup = True
        if self.set_ftp_log(get) == 'stop':
            file_name = self.__messages_file
            is_backup = False
        file_list = self.get_file_list(file_name, is_backup)
        data = []
        sortid = 0
        tmp_dict = {}
        login_all = []
        for file in file_list:

            if not os.path.isfile(file['file']): continue
            conf = public.readFile(file['file'])
            lines = conf.split('\n')
            for line in lines:
                if not line: continue
                login_info = {}
                if search_str not in line and search_str2 not in line:
                    continue
                tmp_value = ' is now logged in'
                info = line[:line.find(search_str)].strip()
                if not info:
                    info = line[:line.find(search_str2)].strip()
                hostname = info.split()[-1]
                exec_time = info.split(hostname)[0].strip()
                exec_time = self.get_format_time(exec_time)
                ip = line[line.find('(') + 1:line.find(')')].split('@')[1]

                #取登录成功日志
                if tmp_value in line:
                    user = line.split(tmp_value)[0].strip().split()[-1]
                    if user == '?' or user != get.user_name: continue
                    dict_index = '{}__{}'.format(user, ip)
                    if dict_index not in tmp_dict:
                        tmp_dict[dict_index] = []
                    tmp_dict[dict_index].append(exec_time)

                #取登出日志
                tmp_value = '[INFO] Logout.'
                tmp_value_two = 'Timeout - try typing a little faster next time'
                if tmp_value in line or tmp_value_two in line:
                    user = line[line.find('(') +
                                1:line.find(')')].split('@')[0]
                    if user == '?' or user != get.user_name: continue
                    dict_index = '{}__{}'.format(user, ip)
                    try:
                        login_info['out_time'] = exec_time
                        login_info['in_time'] = tmp_dict[dict_index][0]
                        login_info['user'] = user
                        login_info['ip'] = ip
                        login_info['status'] = 'Success'  #0为登录失败，1为登录成功
                        login_info['sortid'] = sortid
                        login_all.append(login_info)
                        tmp_dict[dict_index] = []
                        sortid += 1
                    except:
                        pass
                #取登录失败日志
                tmp_value = 'Authentication failed for user'
                if tmp_value in line:
                    user = line.split(tmp_value)[-1].replace('[', '').replace(
                        ']', '').strip()
                    if user == '?' or user != get.user_name: continue
                    login_info['user'] = user
                    login_info['ip'] = ip
                    login_info['status'] = 'Failure'  #0为登录失败，1为登录成功
                    login_info['in_time'] = exec_time
                    login_info['out_time'] = exec_time
                    login_info['sortid'] = sortid
                    login_all.append(login_info)
                    sortid += 1

        if tmp_dict:
            for item in tmp_dict.keys():
                if not tmp_dict[item]: continue
                info = {
                    "status": "login successful",
                    "in_time": tmp_dict[item][0],
                    "out_time": "connecting",
                    "user": item.split('__')[0],
                    "ip": item.split('__')[1],
                    "sortid": sortid
                }
                sortid += 1
                login_all.append(info)
        #搜索过滤
        if login_all and 'search' in get and get.search and get.search.strip():
            for info in login_all:
                try:
                    search_str = str(get.search).strip().lower()
                    # public.writeFile('/tmp/aa.aa', get.search)
                    if info['ip'].find(search_str) != -1 or info['user'].lower(
                    ).find(search_str) != -1 or info['status'].find(
                            search_str) != -1 or info['in_time'].find(
                                search_str) != -1:
                        data.append(info)
                    elif info['out_time'] and info['out_time'].find(
                            search_str) != -1:
                        data.append(info)
                except:
                    pass
        else:
            for info2 in login_all:
                data.append(info2)

        data = sorted(data, key=lambda x: x['sortid'], reverse=True)
        return self.get_page(data, get)

    def get_page(self, data, get):
        """
            @name 取分页
            @author hezhihong
            @param data 需要分页的数据 list
            @param get.p 第几页
            @return 指定分页数据
            """
        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()

        info = {}
        info['count'] = len(data)
        info['row'] = 10
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = {}
        info['return_js'] = ''
        # 获取分页数据
        result = {}
        result['page'] = page.GetPage(info, limit='1,2,3,4,5,8')
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n >= page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result

    def get_action_log(self, get):
        """
        @name 取操作日志
        @author hezhihong
        @param get.user_name ftp用户名
        return {"upload":[],"download":[],"rename":[],"delete":[]}
        """
        search_str = 'pure-ftpd:'
        args = public.dict_obj()
        args.exec_name = 'getlog'
        file_name = self.__ftp_backup_path
        is_backup = True
        if self.set_ftp_log(get) == 'stop':
            file_name = self.__messages_file
            is_backup = False
        file_list = self.get_file_list(file_name, is_backup)
        if not hasattr(get, 'user_name'):
            return public.returnMsg(False, public.lang("The parameter is incorrect！"))
        data = []
        tmp_data = []
        sortid = 0
        for file in file_list:
            if not os.path.isfile(file['file']): continue
            conf = public.readFile(file['file'])
            lines = conf.split('\n')
            for line in lines:
                if not line: continue
                action_info = {}
                if search_str not in line: continue

                tmp_v = line.split(search_str)
                if len(tmp_v[0].strip().split())<3:continue
                hostname = tmp_v[0].strip().split()[3].strip()
                action_time = tmp_v[0].replace(hostname, '').strip()
                action_info['time'] = self.get_format_time(action_time)

                upload_value = ' uploaded '
                download_value = ' downloaded '
                rename_value = 'successfully renamed or moved:'
                delete_value = ' Deleted '
                ip = line[line.find('(') + 1:line.find(')')].split('@')[1]
                action_info['ip'] = ip
                action_info['type'] = ''
                #取操作用户
                user = ''
                if upload_value in line or download_value in line or rename_value in line or delete_value in line:
                    user = line[line.find('(') +
                                1:line.find(')')].split('@')[0]
                    action_info['sortid'] = sortid
                    sortid = sortid + 1
                if not user or user != get.user_name: continue
                #取上传日志
                if (get.type == 'all'
                        or get.type == 'upload') and upload_value in line:
                    line_list = line.split()
                    upload_index = line_list.index('uploaded')
                    # action_info['file'] = line_list[upload_index - 1].replace(
                    #     '//', '/')
                    action_info['file'] = line[line.find(']') +
                                               1:line.rfind('(')].replace(
                                                   'uploaded',
                                                   '').replace('//',
                                                               '/').strip()
                    action_info['type'] = 'upload'
                    tmp_data.append(action_info)
                #取下载日志
                if (get.type == 'all'
                        or get.type == 'download') and download_value in line:
                    line_list = line.split()
                    upload_index = line_list.index('downloaded')
                    action_info['file'] = line_list[upload_index - 1].replace(
                        '//', '/')
                    action_info['type'] = 'download'
                    tmp_data.append(action_info)
                #取重命名日志
                if (get.type == 'all'
                        or get.type == 'rename') and rename_value in line:
                    action_info['file'] = line.split(rename_value)[1].replace(
                        '->', 'Renamed to').strip().replace('//', '/')
                    action_info['type'] = 'rename'
                    tmp_data.append(action_info)
                #取删除日志
                if (get.type == 'all'
                        or get.type == 'delete') and delete_value in line:
                    action_info['file'] = line.split()[-1].strip().replace(
                        '//', '/')
                    action_info['type'] = 'delete'
                    tmp_data.append(action_info)
            # f.close
        #搜索过滤
        if tmp_data and 'search' in get and get.search and get.search.strip():
            for info in tmp_data:
                search_str = str(get.search).strip().lower()
                if info['ip'].find(search_str) != -1 or info['file'].lower(
                ).find(search_str) != -1 or info['type'].find(
                        search_str) != -1 or info['time'].find(
                            search_str) != -1 or get.user_name.lower().find(
                                search_str) != -1:
                    data.append(info)
        else:
            for info2 in tmp_data:
                data.append(info2)
        data = sorted(data, key=lambda x: x['sortid'], reverse=True)
        return self.get_page(data, get)

    def del_crontab(self):
        """
        @name 删除项目定时清理任务
        @auther hezhihong<2022-10-31>
        @return 
        """
        cron_name = '[Do not delete] FTP audit log cutting task'
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        cron_list = public.M('crontab').where("name=?", (cron_name, )).select()
        if cron_list:
            for i in cron_list:
                if not i: continue
                cron_echo = public.M('crontab').where(
                    "id=?", (i['id'], )).getField('echo')
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)
                del_cron_file = cron_path + cron_echo
                public.ExecShell(
                    "crontab -u root -l| grep -v '{}'|crontab -u root -".
                    format(del_cron_file))

    def add_crontab(self):
        """
        @name 构造日志切割任务
        """
        python_path = ''
        try:
            python_path = public.ExecShell('which btpython')[0].strip("\n")
        except:
            try:
                python_path = public.ExecShell('which python')[0].strip("\n")
            except:
                pass
        if not python_path: return False
        if not public.M('crontab').where('name=?',
                                         ('[Do not delete] FTP audit log cutting task', )).count():
            cmd = '{} {}'.format(python_path, self.__script_py)
            args = {
                "name": "[Do not delete] FTP audit log cutting task",
                "type": 'day',
                "where1": '',
                "hour": '0',
                "minute": '1',
                "sName": "",
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True


