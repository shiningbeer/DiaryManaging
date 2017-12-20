# -*- coding:utf-8 -*-

import os
import requests
import json
import datetime
import sys
import logging
from IPy import IP
# 设置默认的level为DEBUG
# 设置log的格式
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s"
)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


class serverCon(object):
    '''
    服务器连接类
    '''

    def __init__(self):
        '''
        构造时配置好各种参数
        '''
        self.SERVER = 'http://127.0.0.1:8000'
        self.URL_REGISTER = '/node/register'
        self.URL_PULSE = '/node/pulse'
        self.URL_SYNCTASKINFO = '/node/syncTaskInfo'
        self.URL_NODETASKCONFIRM = '/node/nodeTaskConfirm'
        self.URL_REPORTTASKCOMPLETE = '/node/reportTaskComplete'
        self.URL_INSTRUCTIONCHANGEDCONFIRM = '/node/instructionChangedConfirm'

        self.PASSWORD = '123'
        self.lasPulseResponse = ""
        self.lasSyncResponse = ""
        self.lasReportResponse = ""

    def setId(self, nodeid):
        '''
        设置id
        '''
        self.NODEID = nodeid

    def register(self):
        url = self.SERVER + self.URL_REGISTER
        p = {'pw': self.PASSWORD}
        r = '服务器连接失败，无法注册。'
        try:
            r = requests.get(url, params=p).text
        # server连接出错
        except:
            logging.info(r)
            return None
        # server返回错误
        if r.startswith("error"):
            logging.info(r)
            return None
        # server返回节点id
        logging.info('注册节点成功，获得id号：%s' % (r))
        return r

    def pulse(self, ipLeft):
        tag = "pulse线程->"
        url = self.SERVER + self.URL_PULSE
        p = {'nodeID': self.NODEID, 'ipLeft': ipLeft}
        r = '无法连接服务器。'
        try:
            r = requests.get(url, params=p).text
        # 连接服务器出错
        except:
            # 判断是否与最后一条相等，不让一直刷屏
            if self.lasPulseResponse != r:
                logging.info(tag + r)
                self.lasPulseResponse = r
            return None
        # 服务器返回错误
        if r.startswith("error"):
            if self.lasPulseResponse != r:
                logging.info(tag + r)
                self.lasPulseResponse = r
            return None
        # 服务器返回无任务
        if r == 'from server: no task now!':
            # 判断是否与最后一条相等，不让一直刷屏
            if self.lasPulseResponse != r:
                logging.info(tag + r)
                self.lasPulseResponse = r
            return None
        # 服务器返回任务信息
        else:
            self.lasPulseResponse = r
            nodeTasks = eval(r)
            logging.info(tag + "接收到%d条任务。" % (len(nodeTasks)))
            return nodeTasks

    def syncTaskInfo(self, ipFinishedList):
        tag = "sync线程->"
        url = self.SERVER + self.URL_SYNCTASKINFO
        jsonstr = json.dumps(ipFinishedList)
        p = {'nodeID': self.NODEID, 'nodeTaskProcess': jsonstr}
        r = '无法连接服务器。'
        try:
            r = requests.get(url, params=p).text
        # 连接服务器出错
        except:
            # 判断是否与最后一条相等，不让一直刷屏
            if self.lasSyncResponse != r:
                logging.info(tag + r)
                self.lasSyncResponse = r
            return None
        # 服务器返回错误
        if r.startswith("error"):
            if self.lasSyncResponse != r:
                logging.info(tag + r)
                self.lasSyncResponse = r
            return None
        # 服务器返回无信息
        if r == 'from server:no task instruction changed!':
            # 判断是否与最后一条相等，不让一直刷屏
            if self.lasSyncResponse != r:
                logging.info(tag + r)
                self.lasSyncResponse = r
            return None
        # 服务器返回同步信息
        else:
            self.lasSyncResponse = r
            instructionChangedTasks = eval(r)
            logging.info(tag + "接收到%d条任务更新指示。" %
                         (len(instructionChangedTasks)))
            return instructionChangedTasks

    def nodeTaskConfirm(self):
        url = self.SERVER + self.URL_NODETASKCONFIRM
        p = {'nodeid': self.NODEID}
        r = '确认接受任务时无法连接服务器。'
        try:
            r = requests.get(url, params=p).text
        # server连接出错
        except:
            logging.info(r)
        # 只打印，不处理返回值
        logging.info(r)

    def instructionChangedConfirm(self):
        url = self.SERVER + self.URL_INSTRUCTIONCHANGEDCONFIRM
        p = {'nodeid': self.NODEID}
        r = '确认接受到任务指令改变时无法连接服务器。'
        try:
            r = requests.get(url, params=p).text
        # server连接出错
        except:
            logging.info(r)
        # 只打印，不处理返回值
        logging.info(r)

    def reportTaskComplete(self, reportList):
        tag = "report线程->"
        r = "没有新任务完成"
        # 如果列表长度为0
        if len(reportList) == 0:
            if self.lasReportResponse != r:
                logging.info(tag + r)
                self.lasReportResponse = r
            return None
        # 如果不为0
        jsonstr = json.dumps(reportList)
        url = self.SERVER + self.URL_REPORTTASKCOMPLETE
        p = {'nodeID': self.NODEID, 'completeList': jsonstr}
        r = '报告任务完成时无法连接服务器。'
        try:
            r = requests.get(url, params=p).text
        # server连接出错
        except:
            # 判断是否与最后一条相等，不让一直刷屏
            if self.lasReportResponse != r:
                logging.info(tag + r)
                self.lasReportResponse = r
            return None
        # server返回错误
        if r.startswith("error"):
            if self.lasReportResponse != r:
                logging.info(tag + r)
                self.lasReportResponse = r
            return None
        # 报告成功
        else:
            if self.lasReportResponse != r:
                logging.info(tag + r)
                self.lasReportResponse = r
            return True
