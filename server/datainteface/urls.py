# -*- coding:utf-8 -*-
from django.conf.urls import url
from . import data

urlpatterns = [
    # 用户
    url(r'^getLogUser/', data.getLogUser),
    # 任务
    url(r'^getTasks/', data.getTasks),
    url(r'^upNewTask/', data.upNewTask),
    url(r'^upDeleteTask/', data.upDeleteTask),
    url(r'^upStartTask/', data.upStartTask),
    url(r'^upStopTask/', data.upStopTask),
    # ip文件
    url(r'^getIpFiles/', data.getIpFiles),
    url(r'^upDeleteIpFile/', data.upDeleteIpFile),
    url(r'^uploadFileIP/', data.uploadFileIP),
    # 插件
    url(r'^getPluginFiles/', data.getPluginFiles),
    url(r'^uploadFilePlugin/', data.uploadFilePlugin),
    url(r'^upDeletePluginFile/', data.upDeletePluginFile),
    # 节点
    url(r'^getActiveNodes/', data.getActiveNodes),

]
