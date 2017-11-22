# -*- coding:utf-8 -*-

import os
import requests
import json
import datetime
import sys
import threading
from dbOperator import dboperator
from dbOperator import statusOptions
import logging
from IPy import IP
# 设置默认的level为DEBUG
# 设置log的格式
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s"
)

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


class Const(object):
    def __init__(self):
        self.id = 'id'
        self.o_id = '_id'
        self.name = 'name'
        self.ipFiles = 'ipFiles'
        self.user = 'user'
        self.description = 'description'
        self.plugin = 'plugin'
        self.pubTime = 'pubTime'
        self.ipTotal = 'ipTotal'
        self.ipFinished = 'ipFinished'
        self.status = 'status'
        self.startTime = 'startTime'
        self.endTime = 'endTime'
        self.ipLeft = 'ipLeft'
        self.pulseTime = 'pulseTime'
        self.nodeId = 'nodeId'
        self.instruction = 'instruction'
        self.instructionChanged = 'instructionChanged'
        self.taskId = 'taskId'
        self.ipRange = 'ipRange'


const = Const()


def iptransformer(iprange):
    # 获取头尾ip
    print iprange
    split = iprange.split('-')
    ipstart = split[0]
    ipend = split[1]

    # 获取头尾的整数
    intStart = IP(ipstart).int()
    intEnd = IP(ipend).int()
    return intStart, intEnd


def func(dbpath, inteval, step, msg):
    '''
    任务执行线程函数，参数说明
    dppath:数据库路径
    inteval:定时器间隔
    step：多少个ip扫描完记录一次进度
    msg:用于控制不重复输出
    '''
    dbo = dboperator(dbpath)
    task = dbo.getOneTaskForExecute()
    if task == None:
        if msg != '目前无可执行任务。':
            logging.info('目前无可执行任务。')
            msg = '目前无可执行任务。'
        # 等一等 再执行
        timer = threading.Timer(inteval, func, (dbpath, inteval, step, msg))
        timer.start()
    else:
        plugin = task[dbo.indexOfPlugin]
        plugin = plugin[0:len(plugin) - 3]
        try:
            exec("from plugin import " + plugin + " as scanning_plugin")
        except:
            logging.info(u'未找到相应插件。')
            # 等一等 再执行
            timer = threading.Timer(
                inteval, func, (dbpath, inteval, step, msg))
            timer.start()
        msg = '有任务了'
        logging.info("开始任务%s" % (task[dbo.indexOfId]))
        ipranges = eval(task[dbo.indexOfIpRange])
        stepcounter = 0  # 每满step个存储一次进度
        for iprange in ipranges:
            print iprange
            start, end = iptransformer(iprange)
            for i in range(start, end + 1):
                # 计数，到step个时，存储扫描到哪里
                stepcounter = stepcounter + 1
                if stepcounter == step:

                    stepcounter = 0
                scanning_plugin.scan("hahaha")
        dbo.updateStatusById(task[dbo.indexOfId], statusOptions['完成'])
        logging.info("完成任务%s" % (task[dbo.indexOfId]))
        # 完成一个后，直接执行下一个
        timer = threading.Timer(0, func, (dbpath, inteval, step, msg))
        timer.start()


class scanNode(object):

    def loadConfig(self):
        self.SERVER = 'http://127.0.0.1:8000'
        self.URL_REGISTER = '/node/register'
        self.URL_PULSE = '/node/pulse'
        self.URL_NODETASKCONFIRM = '/node/nodeTaskConfirm'
        self.PASSWORD = '123'
        self.DBPATH = 'test.db'
        self.PLUGINDIR = 'plugin/'
        self.PULSE_INTEVAL = 10
        self.DOTASK_INTEVAL = 10
        self.STEP_RECORDPROGRESS = 10
        # 获得id
        self.NODEID = self.getid()
        self.lastMsg = ''

    def register(self):
        url = self.SERVER + self.URL_REGISTER
        p = {'pw': self.PASSWORD}
        try:
            r = requests.get(url, params=p).text
        except:
            logging.info(u'无法连接服务器，节点退出。')
            sys.exit()
        if r.startswith("error"):
            logging.info(r)
            sys.exit()

        return r

    def nodeTaskConfirm(self, nodeTaskId):
        url = self.SERVER + self.URL_NODETASKCONFIRM
        p = {'id': nodeTaskId}
        r = '确认任务%s时无法连接服务器。'
        try:
            r = requests.get(url, params=p).text
        except:
            logging.info(r % (nodeTaskId))
        logging.info(r)

    def isPluginExist(self, plugin):
        path = self.PLUGINDIR + plugin
        if os.path.exists(path):
            return True
        else:
            return False
    # 读取配置，如果有id则读出，如果没有则向服务器注册并保存

    def getid(self):
        nodeId = ''
        try:
            f = open('id.txt', 'r')
            nodeId = f.readline()
            f.close()
            logging.info(u'本节点id:' + nodeId)
            return nodeId
        except:
            logging.info(u'本地未找到id.txt，向服务器注册节点。')
            nodeId = self.register()

            f = open('id.txt', 'w')
            f.writelines(nodeId)
            f.close()
            return nodeId

    def doTask(self):
        task = None
        timer = threading.Timer(
            0, func, (self.DBPATH, self.DOTASK_INTEVAL, self.STEP_RECORDPROGRESS, ""))
        timer.start()

    def pulse(self):
        def func():
            url = self.SERVER + self.URL_PULSE
            p = {'nodeID': self.NODEID, 'ipLeft': '0'}
            try:
                r = requests.get(url, params=p).text
                if r.startswith("error"):
                    logging.info(r)
                    return
            except:
                logging.info(u'服务器无响应，5秒后重试。')

            if r != None:
                if r == 'no task now!':
                    # 判断是否相等，不让一直刷屏
                    if r != self.lastMsg:
                        self.lastMsg = r
                        logging.info(r)
                else:
                    self.lastMsg = r
                    nodeTasks = eval(r)
                    logging.info("接收到%d条任务。" % (len(nodeTasks)))

                    # SQLite objects created in a thread can only be used in that same thread.
                    # 所以每个线程都必须新建一个对象
                    dbo = dboperator(self.DBPATH)
                    for task in nodeTasks:
                        ntid = task[const.id]
                        plugin = task[const.plugin]
                        if self.isPluginExist(plugin) != True:
                            logging.info("任务%s所指定的插件%s不存在，请等待下载线程下载，或请直接将相应插件拷入plugin文件夹。" % (
                                ntid, plugin))
                            continue

                        if dbo.isExistById(ntid):
                            logging.info("任务%s已存在，不予保存。" % (ntid))
                            self.nodeTaskConfirm(ntid)
                            continue

                        ipRange = json.dumps(task[const.ipRange])
                        ipTotal = task[const.ipTotal]
                        dbo.insertTask(ntid, ipRange, plugin, ipTotal)
                        logging.info("已保存任务%s，向服务器发送确认信息。" % (ntid))
                        self.nodeTaskConfirm(ntid)
            timer = threading.Timer(self.PULSE_INTEVAL, func)
            timer.start()

        timer = threading.Timer(0, func)
        timer.start()


if __name__ == '__main__':
    node = scanNode()
    node.loadConfig()
    node.pulse()
    node.doTask()
