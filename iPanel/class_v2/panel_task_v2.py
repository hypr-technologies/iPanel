#coding: utf-8
# -------------------------------------------------------------------
# iPanel
# -------------------------------------------------------------------
# Copyright (c) 2019-2099 iPanel(www.iPanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@iPanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 消息队列
# ------------------------------
import json
import time
import public
import sys
import os
import re
from public.validate import Param
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')

class bt_task:
    __table = 'task_list'
    __task_tips = '/dev/shm/bt_task_now.pl'
    __task_path = '/www/server/panel/tmp/'
    down_log_total_file = '/tmp/download_total.pl'
    not_web = False
    def __init__(self):

        # 创建数据表
        sql = '''CREATE TABLE IF NOT EXISTS `task_list` (
  `id`              INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 			INTEGER,
  `shell` 			TEXT,
  `other`           TEXT,
  `exectime` 	  	INTEGER,
  `endtime` 	  	INTEGER,
  `addtime`			INTEGER
);'''
        public.M(None).execute(sql, ())

        # 创建临时目录
        if not os.path.exists(self.__task_path):
            os.makedirs(self.__task_path, 384)

    # 取任务列表
    def get_task_list(self, status=-3):
        sql = public.M(self.__table)
        if status != -3:
            sql = sql.where('status=?', (status,))
        data = sql.field(
            'id,name,type,shell,other,status,exectime,endtime,addtime').select()
        return data

    # 取任务列表前端
    def get_task_lists(self, get):
        # 校验参数
        try:
            get.validate([
                Param('status').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        sql = public.M(self.__table)
        if 'status' in get:
            if get.status == '-3':
                sql = sql.where('status=? OR status=?', (-1, 0))
            else:
                sql = sql.where('status=?', (get.status,))
        data = sql.field('id,name,type,shell,other,status,exectime,endtime,addtime').order(
            'id asc').limit('10').select()
        if type(data) == str:
            public.WriteLog('TASK_QUEUE', data,not_web = self.not_web)
            return public.return_message(0,0,[])
        if not 'num' in get:
            get.num = 15
        num = int(get.num)
        for i in range(len(data)):
            data[i]['log'] = ''
            if data[i]['status'] == -1:
                data[i]['log'] = self.get_task_log(
                    data[i]['id'], data[i]['type'], num)
            elif data[i]['status'] == 1:
                data[i]['log'] = self.get_task_log(
                    data[i]['id'], data[i]['type'], 10)
            if data[i]['type'] == '3':
                data[i]['other'] = json.loads(data[i]['other'])
        return public.return_message(0,0,data)

    # 创建任务
    def create_task(self, task_name, task_type, task_shell, other=''):
        self.clean_log()
        task_id = public.M(self.__table).add('name,type,shell,other,addtime,status',
                                   (task_name, task_type, task_shell, other, int(time.time()), 0))
        public.WriteFile(self.__task_tips, 'True')
        public.ExecShell("/etc/init.d/bt start")
        if not public.M(self.__table).where('status=?', ('-1',)).count():
            tip_file = "/dev/shm/.start_task.pl"
            tip_time = public.readFile(tip_file)
            if not tip_time or time.time() - int(tip_time) > 600:
                public.ExecShell("/www/server/panel/BT-Task")
                public.print_log("Background task restarted")
        return task_id

    # 修改任务
    def modify_task(self, id, key, value):
        public.M(self.__table).where('id=?', (id,)).setField(key, value)
        return True

    # 删除任务
    def remove_task(self, get):
        task_info = self.get_task_find(get.id)
        public.M(self.__table).where('id=?', (get.id,)).delete()
        if str(task_info['status']) == '-1':
            public.ExecShell(
                "kill -9 $(ps aux|grep 'task.py'|grep -v grep|awk '{print $2}')")
            if task_info['type'] == '1':
                public.ExecShell(
                    "kill -9 $(ps aux|grep '{}')".format(task_info['other']))
                time.sleep(1)
                if os.path.exists(task_info['other']):
                    os.remove(task_info['other'])
            elif task_info['type'] == '3':
                z_info = json.loads(task_info['other'])
                if z_info['z_type'] == 'tar.gz':
                    public.ExecShell(
                        "kill -9 $(ps aux|grep 'tar -zcvf'|grep -v grep|awk '{print $2}')")
                elif z_info['z_type'] == 'rar':
                    public.ExecShell(
                        "kill -9 $(ps aux|grep /www/server/rar/rar|grep -v grep|awk '{print $2}')")
                elif z_info['z_type'] == 'zip':
                    public.ExecShell(
                        "kill -9 $(ps aux|grep '.zip -r'|grep -v grep|awk '{print $2}')")
                    public.ExecShell(
                        "kill -9 $(ps aux|grep '.zip\' -r'|grep -v grep|awk '{print $2}')")
                if os.path.exists(z_info['dfile']):
                    os.remove(z_info['dfile'])
            elif task_info['type'] == '2':
                public.ExecShell(
                    "kill -9 $(ps aux|grep 'tar -zxvf'|grep -v grep|awk '{print $2}')")
                public.ExecShell(
                    "kill -9 $(ps aux|grep '/www/server/rar/unrar'|grep -v grep|awk '{print $2}')")
                public.ExecShell(
                    "kill -9 $(ps aux|grep 'unzip -P'|grep -v grep|awk '{print $2}')")
                public.ExecShell(
                    "kill -9 $(ps aux|grep 'gunzip -c'|grep -v grep|awk '{print $2}')")
            elif task_info['type'] == '0':
                public.ExecShell(
                    "kill -9 $(ps aux|grep '"+task_info['shell']+"'|grep -v grep|awk '{print $2}')")

            public.ExecShell("/etc/init.d/bt start")
        return public.return_msg_gettext(True, public.lang("Task cancelled!"))

    # 取一条任务
    def get_task_find(self, id):
        data = public.M(self.__table).where('id=?', (id,)).field(
            'id,name,type,shell,other,status,exectime,endtime,addtime').find()
        return data

    # 执行任务
    # task_type  0.执行shell  1.下载文件  2.解压文件  3.压缩文件
    def execute_task(self, id, task_type, task_shell, other=''):
        if not os.path.exists(self.__task_path):
            os.makedirs(self.__task_path, 384)
        log_file = self.__task_path + str(id) + '.log'

        # 标记状态执行时间
        self.modify_task(id, 'status', -1)
        self.modify_task(id, 'exectime', int(time.time()))
        task_type = int(task_type)
        # 开始执行
        if task_type == 0:  # 执行命令
            public.ExecShell(task_shell + ' &> ' + log_file)
        elif task_type == 1:  # 下载文件
            if os.path.exists(self.down_log_total_file):
                os.remove(self.down_log_total_file)
            public.ExecShell(
                "wget -O '{}' '{}' --no-check-certificate -T 30 -t 5 -d &> {}".format(other, task_shell, log_file))
            if os.path.exists(log_file):
                os.remove(log_file)
        elif task_type == 2:  # 解压文件
            zip_info = json.loads(other)
            self._unzip(task_shell, zip_info['dfile'],
                        zip_info['password'], log_file)
        elif task_type == 3:  # 压缩文件
            zip_info = json.loads(other)
            if not 'z_type' in zip_info:
                zip_info['z_type'] = 'tar.gz'
            print(self._zip(
                task_shell, zip_info['sfile'], zip_info['dfile'], log_file, zip_info['z_type']))
        elif task_type == 4:  # 备份数据库
            self.backup_database(task_shell, log_file)
        elif task_type == 5:  # 导入数据库
            self.input_database(task_shell, other, log_file)
        elif task_type == 6:  # 备份网站
            self.backup_site(task_shell, log_file)
        elif task_type == 7:  # 恢复网站
            pass
        # 标记状态与结束时间
        self.modify_task(id, 'status', 1)
        self.modify_task(id, 'endtime', int(time.time()))

    # 开始检测任务
    def start_task(self):
        noe = False
        n = 0
        tip_file = '/dev/shm/.start_task.pl'
        while True:
            try:
                time.sleep(1)
                public.writeFile(tip_file, str(int(time.time())))
                n += 1
                if not os.path.exists(self.__task_tips) and noe and n < 60:
                    continue
                if os.path.exists(self.__task_tips):
                    os.remove(self.__task_tips)
                n = 0
                public.M(self.__table).where(
                    'status=?', ('-1',)).setField('status', 0)
                task_list = self.get_task_list(0)
                for task_info in task_list:
                    self.execute_task(
                        task_info['id'], task_info['type'], task_info['shell'], task_info['other'])
                noe = True
            except:
                print(public.get_error_info())

    # 前端通过任务ID取某一个任务的日志
    def get_task_log_by_id(self, get):
        task_id = get.id
        task_type = get.task_type
        log_data = {}
        if "num" in get:
            num = int(get.num)
            log_data = self.get_task_log(task_id, task_type, num)
        else:
            log_data = self.get_task_log(task_id, task_type)
        task_obj = self.get_task_find(task_id)
        log_data["status"] = task_obj["status"]
        return log_data

    # 取任务执行日志
    def get_task_log(self, id, task_type, num=5):
        log_file = self.__task_path + str(id) + '.log'
        if not os.path.exists(log_file):
            data = ''
            if(task_type == '1'):
                data = {'name': public.lang("Download file"), 'total': 0, 'used': 0,
                        'pre': 0, 'speed': 0, 'time': 0}
            return data

        if(task_type == '1'):
            total = 0
            if not os.path.exists(self.down_log_total_file):
                f = open(log_file, 'r')
                head = f.read(4096)
                content_length = re.findall(r"Length:\s+(\d+)", head)
                if content_length:
                    total = int(content_length[0])
                    public.writeFile(self.down_log_total_file,
                                     content_length[0])
            else:
                total = public.readFile(self.down_log_total_file)
                if not total:
                    total = 0
                total = int(total)

            filename = public.M(self.__table).where(
                'id=?', (id,)).getField('shell')

            speed_tmp = public.ExecShell("tail -n 2 {}".format(log_file))[0]
            speed_total = re.findall(
                r"([\d\.]+[BbKkMmGg]).+\s+(\d+)%\s+([\d\.]+[KMBGkmbg])\s+(\w+[sS])", speed_tmp)
            if not speed_total:
                data = {'name':public.get_msg_gettext('Download file {}',(filename,)),'total':0,'used':0,'pre':0,'speed':0,'time':0}
            else:
                speed_total = speed_total[0]
                used = speed_total[0]
                if speed_total[0].lower().find('k') != -1:
                    used = public.to_size(
                        float(speed_total[0].lower().replace('k', '')) * 1024)
                    u_time = speed_total[3].replace(
                        'h', 'Hour').replace('m', 'Minute').replace('s', 'Second')
                data = {'name': public.get_msg_gettext('Download file {}',(filename,)),'total': total, 'used': used, 'pre': speed_total[1], 'speed': speed_total[2], 'time': u_time}
        else:
            data = public.ExecShell("tail -n {} {}".format(num, log_file))[0]
            if type(data) == list:
                return ''
            if isinstance(data,bytes):
                data = data.decode('utf-8')
            data = data.replace('\x08', '').replace('\n', '<br>')
        return data

    # 清理任务日志
    def clean_log(self):
        import shutil
        s_time = int(time.time())
        timeout = 86400
        for f in os.listdir(self.__task_path):
            filename = self.__task_path + f
            c_time = os.stat(filename).st_ctime
            if s_time - c_time > timeout:
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
        return True

    # 文件压缩
    def _zip(self, path, sfile, dfile, log_file, z_type='tar.gz'):
        if sys.version_info[0] == 2:
            sfile = sfile.encode('utf-8')
            dfile = dfile.encode('utf-8')
        if sys.version_info[0] == 2:
            path = path.encode('utf-8')
        if sfile.find(',') == -1:
            if not os.path.exists(path+'/'+sfile):
                return public.return_msg_gettext(False, public.lang("Configuration file not exist"))
        # 处理多文件压缩
        sfiles = ''
        for sfile in sfile.split(','):
            if not sfile:
                continue
            sfiles += " '" + sfile + "'"

        # 判断压缩格式
        if z_type == 'zip':
            public.ExecShell("cd '"+path+"' && zip '"+dfile +
                             "' -r "+sfiles+" &> "+log_file)
        elif z_type == 'tar.gz':
            public.ExecShell("cd '" + path + "' && tar -zcvf '" +
                             dfile + "' " + sfiles + " &> " + log_file)
        elif z_type == 'rar':
            rar_file = '/www/server/rar/rar'
            if not os.path.exists(rar_file):
                self.install_rar()
            public.ExecShell("cd '" + path + "' && "+rar_file +
                             " a -r '" + dfile + "' " + sfiles + " &> " + log_file)
        elif z_type == '7z':
            _7z_bin = self.get_7z_bin()
            if not _7z_bin:
                self.install_7zip()
                err_msg = 'The p7zip component is not installed, an automatic installation has been attempted, please wait a few minutes and try again!'
                public.WriteLog("File manager","Failed to compress file, reason: {}, file: {}".format(err_msg,sfile))
                return public.returnMsg(False, err_msg)
            public.ExecShell("cd {} && {} a -t7z {} {} -y &> {}".format(path, _7z_bin, dfile, sfiles, log_file))
        else:
            return public.return_msg_gettext(False, public.lang("Specified compression format is not supported!"))

        self.set_file_accept(dfile)
        #public.WriteLog("TYPE_FILE", 'Compression succeeded!', (sfiles, dfile),not_web = self.not_web)
        public.write_log_gettext("File manager", 'Compressed file [ {} ] to [ {} ] success', (sfiles, dfile))
        return public.return_msg_gettext(True, public.lang("Compression succeeded!"))

    # 文件解压
    def _unzip(self, sfile, dfile, password, log_file):
        if sys.version_info[0] == 2:
            sfile = sfile.encode('utf-8')
            dfile = dfile.encode('utf-8')
        if not os.path.exists(sfile):
            return public.return_msg_gettext(False, public.lang("Configuration file not exist"))

        # 判断压缩包格式
        if sfile[-4:] == '.zip':
            public.ExecShell("unzip -P '"+password+"' -o '" +
                             sfile + "' -d '" + dfile + "' &> " + log_file)
        elif sfile[-7:] == '.tar.gz' or sfile[-4:] == '.tgz':
            public.ExecShell("tar zxvf '" + sfile +
                             "' -C '" + dfile + "' &> " + log_file)
        elif sfile[-4:] == '.rar':
            rar_file = '/www/server/rar/unrar'
            if not os.path.exists(rar_file):
                self.install_rar()
            pass_opt = '-p-'
            if password:
                password = password.replace("&",r"\&").replace('"','\"')
                pass_opt = '-p"{}"'.format(password)

            public.ExecShell(rar_file + ' x '+ pass_opt +' -u -y "' + sfile + '" "' + dfile + '" &> ' + log_file)

        elif sfile[-4:] == '.war':
            public.ExecShell("unzip -P '"+password+"' -o '" +
                             sfile + "' -d '" + dfile + "' &> " + log_file)
        elif sfile[-4:] == '.bz2':
            public.ExecShell("tar jxvf '" + sfile +
                             "' -C '" + dfile + "' &> " + log_file)
        elif sfile[-3:] == '.7z':
            _7zbin = self.get_7z_bin()
            if not _7zbin:
                self.install_7zip()
                err_msg = 'The p7zip component is not installed, an automatic installation has been attempted, please wait a few minutes and try again!'
                public.WriteLog("File manager","Failed to compress file, reason: {}, file: {}".format(err_msg,sfile))
                return public.returnMsg(False, err_msg)
            pass_opt = ""
            if password:
                pass_opt = '-p"{}"'.format(password)
            public.ExecShell('{} x "{}" -o"{}" -y {} &> {}'.format(_7zbin,sfile,dfile,pass_opt,log_file))
        else:
            public.ExecShell("gunzip -c " + sfile + " > " + sfile[:-3])

        # 异常处理
        log_msg = public.readFile(log_file)
        err_msg = None
        if log_msg:
            if log_msg.find("incorrect password") != -1 \
                or log_msg.find("The specified password is incorrect.") != -1 \
                or log_msg.find("Data Error in encrypted file. Wrong password") != -1:
                err_msg = 'Decompression password error!'
                public.WriteLog("File manager","Unzip file failed, reason: {}, file: {}".format(err_msg,sfile))
            elif log_msg.find("unsupported compression method 99") != -1:
                err_msg = 'Unsupported Zip encryption and compression, only ZIP traditional encryption is supported for ZIP archives!'
                public.WriteLog("File manager","Unzip file failed, reason: {}, file: {}".format(err_msg,sfile))
            elif log_msg.find("is not RAR archive") != -1:
                err_msg = "It is not a rar archive, check whether to modify the file with the extension rar for other compression formats!"
                public.WriteLog("File manager","Unzip file failed, reason: {}, file: {}".format(err_msg,sfile))
            elif log_msg.find("gzip: stdin") != -1:
                public.ExecShell("tar xvf '" + sfile + "' -C '" + dfile + "' &> " + log_file)

        if err_msg: return public.returnMsg(False, err_msg)

        # 检查是否设置权限
        if self.check_dir(dfile):
            sites_path = public.M('config').where(
                'id=?', (1,)).getField('sites_path')
            if dfile.find('/www/wwwroot') != -1 or dfile.find(sites_path) != -1:
                self.set_file_accept(dfile)
            else:
                import pwd
                user = pwd.getpwuid(os.stat(dfile).st_uid).pw_name
                public.ExecShell("chown %s:%s %s" % (user, user, dfile))

        #public.WriteLog("TYPE_FILE", 'Uncompression succeeded!', (sfile, dfile),not_web = self.not_web)
        public.write_log_gettext("File manager", 'unzip file [ {} ] -> [ {} ] success', (sfile, dfile))
        return public.return_msg_gettext(True, public.lang("Uncompression succeeded!"))

    def get_7z_bin(self):
        '''
            @name 获取7z命令路径
            @author hwliang
            @return {string} 7z命令路径
        '''
        _7z_bins = ["/usr/bin/7z","/usr/bin/7za","/usr/bin/7zr"]
        for _7z_bin in _7z_bins:
            if os.path.exists(_7z_bin):
                return _7z_bin
        return None

    def install_7zip(self):
        '''
            @name 安装7zip
            @author hwliang
            @return {bool} True/False
        '''
        _7z_bin = self.get_7z_bin()
        if _7z_bin:
            return True

        # 是否已经尝试安装过
        install_tip = '{}/data/7z_install.pl'.format(public.get_panel_path())
        if os.path.exists(install_tip):
            return False

        if os.path.exists("/usr/bin/apt-get"):
            public.ExecShell("nohup apt-get -y install p7zip-full &> /dev/null &")
        elif os.path.exists("/usr/bin/yum"):
            public.ExecShell("nohup yum -y install p7zip &> /dev/null &")
        elif os.path.exists("/usr/bin/dnf"):
            public.ExecShell("nohup dnf -y install p7zip &> /dev/null &")
        else:
            return False
        return True

    # 备份网站
    def backup_site(self, id, log_file):
        find = public.M('sites').where(
            "id=?", (id,)).field('name,path,id').find()
        fileName = find['name']+'_' + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime())+'.zip'
        backupPath = public.M('config').where(
            'id=?', (1,)).getField('backup_path') + '/site'

        zipName = backupPath + '/'+fileName
        if not (os.path.exists(backupPath)):
            os.makedirs(backupPath)

        execStr = "cd '" + find['path'] + "' && zip '" + \
            zipName + "' -x .user.ini -r ./ &> " + log_file
        public.ExecShell(execStr)

        sql = public.M('backup').add('type,name,pid,filename,size,addtime',
                                     (0, fileName, find['id'], zipName, 0, public.getDate()))
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS', (find['name'],),not_web = self.not_web)
        return public.return_msg_gettext(True, public.lang("Backup Succeeded!"))

    # 备份数据库
    def backup_database(self, id, log_file):
        name = public.M('databases').where("id=?", (id,)).getField('name')
        find = public.M('config').where('id=?', (1,)).field(
            'mysql_root,backup_path').find()

        if not os.path.exists(find['backup_path'] + '/database'):
            public.ExecShell('mkdir -p ' + find['backup_path'] + '/database')
        self.mypass(True, find['mysql_root'])

        fileName = name + '_' + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql.gz'
        backupName = find['backup_path'] + '/database/' + fileName
        public.ExecShell("/www/server/mysql/bin/mysqldump --force --opt \"" +
                         name + "\" | gzip > " + backupName)
        if not os.path.exists(backupName):
            return public.return_msg_gettext(False, public.lang("Backup error!"))

        self.mypass(False, find['mysql_root'])

        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        sql.add('type,name,pid,filename,size,addtime',
                (1, fileName, id, backupName, 0, addTime))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (name,),not_web = self.not_web)
        return public.return_msg_gettext(True, public.lang("Backup Succeeded!"))

    # 导入数据库
    def input_database(self, id, file, log_file):
        name = public.M('databases').where("id=?", (id,)).getField('name')
        root = public.M('config').where('id=?', (1,)).getField('mysql_root')
        tmp = file.split('.')
        exts = ['sql', 'gz', 'zip']
        ext = tmp[len(tmp) - 1]
        if ext not in exts:
            return public.return_msg_gettext(False, public.lang("Select sql/gz/zip file!"))

        isgzip = False
        if ext != 'sql':
            tmp = file.split('/')
            tmpFile = tmp[len(tmp)-1]
            tmpFile = tmpFile.replace('.sql.' + ext, '.sql')
            tmpFile = tmpFile.replace('.' + ext, '.sql')
            tmpFile = tmpFile.replace('tar.', '')
            backupPath = public.M('config').where(
                'id=?', (1,)).getField('backup_path') + '/database'

            if ext == 'zip':
                public.ExecShell("cd " + backupPath + " && unzip " + file)
            else:
                public.ExecShell("cd " + backupPath + " && tar zxf " + file)
                if not os.path.exists(backupPath + "/" + tmpFile):
                    public.ExecShell("cd " + backupPath +
                                     " && gunzip -q " + file)
                    isgzip = True

            if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '':
                return public.return_msg_gettext(False, 'Configuration file not exist', (tmpFile,))
            self.mypass(True, root)
            public.ExecShell(public.GetConfigValue('setup_path') + "/mysql/bin/mysql -uroot -p" +
                             root + " --force \"" + name + "\" < " + backupPath + '/' + tmpFile)
            self.mypass(False, root)
            if isgzip:
                public.ExecShell('cd ' + backupPath +
                                 ' && gzip ' + file.split('/')[-1][:-3])
            else:
                public.ExecShell("rm -f " + backupPath + '/' + tmpFile)
        else:
            self.mypass(True, root)
            public.ExecShell(public.GetConfigValue(
                'setup_path') + "/mysql/bin/mysql -uroot -p" + root + " --force \"" + name + "\" < " + file)
            self.mypass(False, root)

        public.WriteLog("TYPE_DATABASE", 'Successfully imported database [{}]', (name,),not_web = self.not_web)
        return public.return_msg_gettext(True, public.lang("Successfully imported database!"))

    # 配置
    def mypass(self, act, root):
        my_cnf = '/etc/my.cnf'
        public.ExecShell("sed -i '/user=root/d' " + my_cnf)
        public.ExecShell("sed -i '/password=/d' " + my_cnf)
        if act:
            mycnf = public.readFile(my_cnf)
            rep = "\\[mysqldump\\]\nuser=root"
            sea = "[mysqldump]\n"
            subStr = sea + "user=root\npassword=\"" + root + "\"\n"
            mycnf = mycnf.replace(sea, subStr)
            if len(mycnf) > 100:
                public.writeFile(my_cnf, mycnf)

    # 设置权限
    def set_file_accept(self, filename):
        # public.ExecShell('chown -R www:www ' + filename)
        # public.ExecShell('chmod -R 755 ' + filename)
        import files
        from collections import namedtuple
        get = namedtuple('get',['path'])
        get.path = filename
        files.files().fix_permissions(get)

    # 检查敏感目录
    def check_dir(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]

        nDirs = ('',
                 '/',
                 '/*',
                 '/www',
                 '/root',
                 '/boot',
                 '/bin',
                 '/etc',
                 '/home',
                 '/dev',
                 '/sbin',
                 '/var',
                 '/usr',
                 '/tmp',
                 '/sys',
                 '/proc',
                 '/media',
                 '/mnt',
                 '/opt',
                 '/lib',
                 '/srv',
                 '/selinux',
                 '/www/server',
                 '/www/server/data',
                 public.GetConfigValue('logs_path'),
                 public.GetConfigValue('setup_path'))

        return not path in nDirs

    # 安装rar组件
    def install_rar(self):
        unrar_file = '/www/server/rar/unrar'
        rar_file = '/www/server/rar/rar'
        bin_unrar = '/usr/local/bin/unrar'
        bin_rar = '/usr/local/bin/rar'
        if os.path.exists(unrar_file) and os.path.exists(bin_unrar):
            try:
                import rarfile
            except:
                public.ExecShell("pip install rarfile")
            return True

        import platform
        os_bit = ''
        if platform.machine() == 'x86_64':
            os_bit = '-x64'
        download_url = public.get_url() + '/src/rarlinux'+os_bit+'-5.6.1.tar.gz'

        tmp_file = '/tmp/bt_rar.tar.gz'
        public.ExecShell('wget -O ' + tmp_file + ' ' + download_url)
        if os.path.exists(unrar_file):
            public.ExecShell("rm -rf /www/server/rar")
        public.ExecShell("tar xvf " + tmp_file + ' -C /www/server/')
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        if not os.path.exists(unrar_file):
            return False

        if os.path.exists(bin_unrar):
            os.remove(bin_unrar)
        if os.path.exists(bin_rar):
            os.remove(bin_rar)

        public.ExecShell('ln -sf ' + unrar_file + ' ' + bin_unrar)
        public.ExecShell('ln -sf ' + rar_file + ' ' + bin_rar)
        #public.ExecShell("pip install rarfile")
        return True


if __name__ == '__main__':
    p = bt_task()
    #p.create_task('测试执行SHELL',0,'yum install wget -y','')
    # print(p.get_task_list())
    # p.modify_task(3,'status',0)
    #p.modify_task(3,'shell','bash /www/server/panel/install/install_soft.sh 0 update php 5.6')
    # p.modify_task(1,'other','{"sfile":"BTPanel","dfile":"/www/test.rar","z_type":"rar"}')
    p.start_task()
    # p._zip(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])


