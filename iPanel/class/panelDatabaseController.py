#coding: utf-8
#-------------------------------------------------------------------
# iPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 iPanel(www.iPanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@iPanel.com>
#-------------------------------------------------------------------

#------------------------------
# 数据库管理控制器
#------------------------------
import os,sys,public,json,re

class DatabaseController:


    def __init__(self):
        pass

    def model(self,args):
        '''
            @name 调用指定项目模型
            @author hwliang<2021-12-31>
            @param args<dict_obj> {
                mod_name: string<模型名称>
                def_name: string<方法名称>
                data: JSON
            }
        '''
        try: # 表单验证
            if args['mod_name'] in ['base']: return public.return_status_code(1000,'Bad call!')
            public.exists_args('def_name,mod_name',args)
            if args['def_name'].find('__') != -1: return public.return_status_code(1000,'The called method name cannot contain the "__" character')
            if not re.match(r"^\w+$",args['mod_name']): return public.return_status_code(1000,r'The called module name cannot contain characters other than \w')
            if not re.match(r"^\w+$",args['def_name']): return public.return_status_code(1000,r'The called module name cannot contain characters other than \w')
        except:
            return public.get_error_object()
        # 参数处理
        module_name = args['mod_name'].strip()
        mod_name = "{}Model".format(args['mod_name'].strip())
        def_name = args['def_name'].strip()

        # # 指定模型是否存在
        # mod_file = "{}/databaseModel/{}.py".format(public.get_class_path(),mod_name)
        # if not os.path.exists(mod_file):
        #     return public.return_status_code(1003,mod_name)
        # # 实例化
        # def_object = public.get_script_object(mod_file)
        # if not def_object: return public.return_status_code(1000,'没有找到{}模型'.format(mod_name))
        # run_object = getattr(def_object.main(),def_name,None)

        # if not run_object: return public.return_status_code(1000,'没有在{}模型中找到{}方法'.format(mod_name,def_name))
        if not hasattr(args,'data'): args.data = {}
        if args.data:
            if isinstance(args.data,str):
                try: # 解析为dict_obj
                    pdata = public.to_dict_obj(json.loads(args.data))
                except:
                    return public.get_error_object()
            elif isinstance(args.data,dict):
                pdata = public.to_dict_obj(args.data)
            else:
                pdata = args.data
        else:
            pdata = public.dict_obj()

        if isinstance(pdata,dict): pdata =  public.to_dict_obj(pdata)
        pdata.model_index = 'database'

        # 前置HOOK
        hook_index = '{}_{}_LAST'.format(mod_name.upper(),def_name.upper())
        hook_result = public.exec_hook(hook_index,pdata)
        if isinstance(hook_result,public.dict_obj):
            pdata = hook_result # 桥接
        elif isinstance(hook_result,dict):
            return hook_result # 响应具体错误信息
        elif isinstance(hook_result,bool):
            if not hook_result: # 直接中断操作
                return public.return_data(False,{},error_msg='Pre-HOOK interrupt operation')

        # 调用处理方法
        # result = run_object(pdata)
        import PluginLoader
        result = PluginLoader.module_run(module_name,def_name,pdata)
        if isinstance(result,dict):
            if 'status' in result and result['status'] == False and 'msg' in result:
                if isinstance(result['msg'],str):
                    if result['msg'].find('Traceback ') != -1:
                        raise public.PanelError(result['msg'])

        # 后置HOOK
        hook_index = '{}_{}_END'.format(mod_name.upper(),def_name.upper())
        hook_data = public.to_dict_obj({
            'args': pdata,
            'result': result
        })
        hook_result = public.exec_hook(hook_index,hook_data)
        if isinstance(hook_result,dict):
            result = hook_result['result']
        return result




