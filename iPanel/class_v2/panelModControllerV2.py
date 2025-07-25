# coding: utf-8
# -------------------------------------------------------------------
# iPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 iPanel(http:#hypr.local) All rights reserved.
# -------------------------------------------------------------------
# Author: hezhihong
# -------------------------------------------------------------------

# ------------------------------
# 网站模型管理控制器
# ------------------------------
import json
import public
import re


class Controller:

    def __init__(self):
        pass

    def model(self, args):
        '''
            @name 调用指定项目模型
            @author hezhihong
            @param {"mod_name":"string<模型名称>","def_name":"string<方法名称>","data":JSON,} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:  # 表单验证
            if args['mod_name'] in ['base']: return public.return_status_code(1000, '错误的调用!')
            public.exists_args('def_name,mod_name', args)
            if args['def_name'].find('__') != -1: return public.return_status_code(1000,
                                                                                   '调用的方法名称中不能包含“__”字符')
            if not re.match(r"^\w+$", args['mod_name']): return public.return_status_code(1000,
                                                                                          r'调用的模块名称中不能包含\w以外的字符')
            if not re.match(r"^\w+$", args['def_name']): return public.return_status_code(1000,
                                                                                          r'调用的方法名称中不能包含\w以外的字符')
        except:
            return public.get_error_object()
        # 参数处理
        module_name = args['mod_name'].strip()
        sub_mod_name = args['sub_mod_name'].strip()
        mod_name = "{}Mod".format(args['mod_name'].strip())
        def_name = args['def_name'].strip()
        model_index = None
        if 'model_index' in args: model_index = args['model_index']

        if not hasattr(args, 'data'): args.data = {}
        if args.data:
            if isinstance(args.data, str):
                try:  # 解析为dict_obj
                    pdata = public.to_dict_obj(json.loads(args.data))
                except:
                    return public.get_error_object()
            else:
                pdata = args.data
        else:
            pdata = args

        if isinstance(pdata, dict):
            pdata = public.to_dict_obj(pdata)

        if not isinstance(pdata, public.dict_obj):
            return public.return_error("传递的参数不是通用的内部对象")

        # 告诉加载器，要加载什么模块
        if model_index: pdata.model_index = model_index

        # 前置HOOK
        hook_index = '{}_{}_LAST'.format(mod_name.upper(), def_name.upper())
        hook_result = public.exec_hook(hook_index, pdata)
        if isinstance(hook_result, public.dict_obj):
            pdata = hook_result  # 桥接
        elif isinstance(hook_result, dict):
            return hook_result  # 响应具体错误信息
        elif isinstance(hook_result, bool):
            if not hook_result:  # 直接中断操作
                return public.return_data(False, {}, error_msg='前置HOOK中断操作')

        # 调用处理方法
        # result = run_object(pdata)
        # import PluginLoader
        
        # public.print_log('mol--v2---module_fuile:{}'.format("{}/{}".format(module_name, sub_mod_name)))
        # result = PluginLoader.module_run("{}/{}".format(module_name, sub_mod_name), def_name, pdata)
        # public.print_log('mol--v2---result:{}'.format(result)
        
        import public.PluginLoader as plugin_loader
        mod_file = '{}/class_v2/modModelV2/project/{}/comMod.py'.format(public.get_panel_path(),module_name)
        public.print_log('mol--v2---mod_file:{}'.format(mod_file))
        plugin_class = plugin_loader.get_module(mod_file)
        public.print_log('mol--v2---plugin_class:{}'.format(plugin_class))
        class_string='main'
        # if mod_name=='ftpModel':
        #     class_string='ftplog'
        plugin_object = getattr(plugin_class,class_string)()
        public.print_log('mol--v2---plugin_object:{}'.format(plugin_object))
        result = getattr(plugin_object,def_name)(pdata)
        public.print_log('mol--v2---result:{}'.format(result))
        
        if isinstance(result, dict):
            if 'status' in result and result['status'] == False and 'msg' in result:
                if isinstance(result['msg'], str):
                    if result['msg'].find('Traceback ') != -1:
                        raise public.PanelError(result['msg'])

        # 后置HOOK
        hook_index = '{}_{}_END'.format(mod_name.upper(), def_name.upper())
        hook_data = public.to_dict_obj({
            'args': pdata,
            'result': result
        })
        hook_result = public.exec_hook(hook_index, hook_data)
        if isinstance(hook_result, dict):
            result = hook_result['result']
        return result


