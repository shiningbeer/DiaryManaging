# -*- coding:utf-8 -*-

import os
import requests
import json
import datetime
import sys
import threading
from dbOperator import dboperator, statusOptions, instructionOptions
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
    split = iprange.split('-')
    ipstart = split[0]
    ipend = split[1]

    # 获取头尾的整数
    intStart = IP(ipstart).int()
    intEnd = IP(ipend).int()
    return intStart, intEnd


def caculateScaningIpRange(ipranges, lastip):
    '''
    根据提供的ipranges列表和上次扫描到的ip，计算出新的扫描ip列表，已经扫描的个数
    '''

    theWholeRange = []
    ipOkCount = 0
    for iprange in ipranges:
        start, end = iptransformer(iprange)
        theWholeRange.append((start, end))
    if lastip == None:  # 如果没有lastip，说明是全新任务，返回全部ip
        return theWholeRange, ipOkCount
    else:  # 已有进度
        int_lastip = IP(lastip).int() + 1
        ipRangesForScan = []
        for iprange in theWholeRange:
            start, end = iprange
            if int_lastip not in range(start, end + 1):
                ipOkCount = ipOkCount + end + 1 - start
                continue
            else:
                ipRangeForscan = (int_lastip, end)
                ipRangesForScan.append(ipRangeForscan)
                ipOkCount = ipOkCount + int_lastip - start
                continue
            ipRangesForScan.append((start, end))
            ipOkCount = ipOkCount + end + 1 - start
        # 如果整个ipranges都找不到lastip，则不知道出了什么错，但不能返回空集，返回整个ipranges
        if len(ipRangesForScan) == 0:
            return theWholeRange, 0
        # 找到lastip，返回子集
        return ipRangesForScan, ipOkCount


def func(dbpath, inteval, step, printed):
    '''
    任务执行线程函数，参数说明
    dppath:数据库路径
    inteval:定时器间隔
    step：多少个ip扫描完记录一次进度
    printed:上次是否打印了no task信息，bool值
    '''
    dbo = dboperator(dbpath)
    task = dbo.getOneTaskForExecute()
    if task == None:
        if printed != True:
            logging.info('目前无可执行任务。')
            printed = True
        # 等一等 再执行
        timer = threading.Timer(
            inteval, func, (dbpath, inteval, step, printed))
        timer.start()
    else:
        nodeTaskId, plugin, ipranges_str, iptotal = task  # 获取task各字段（task是个元组）
        # 把后缀名.py去掉
        plugin = plugin[0:len(plugin) - 3]
        try:
            exec("from plugin import " + plugin + " as scanning_plugin")
        except:
            logging.info(u'未找到相应插件。')
            # 等一等 再执行
            timer = threading.Timer(
                inteval, func, (dbpath, inteval, step, printed))
            timer.start()
        printed = False
        logging.info("开始任务%s" % (nodeTaskId))
        ipranges = eval(ipranges_str)  # 获取ip集
        lastip = dbo.getLastIpById(nodeTaskId)  # 加载执行进度

        # 计算需要扫描的ip集,已经扫描的个数
        ipRangesForScan, ipOkCount = caculateScaningIpRange(
            ipranges, lastip)
        stepcounter = 0  # 每满step个存储一次进度
        for iprange in ipRangesForScan:
            start, end = iprange
            for i in range(start, end + 1):
                # 计数，到step个时，存储扫描到哪里,扫描了几个
                stepcounter = stepcounter + 1
                ipOkCount = ipOkCount + 1
                scanning_plugin.scan(str(IP(i)))
                if stepcounter == step:
                    dbo.updateLastIpById(nodeTaskId, str(IP(i)))  # 保存执行进度
                    dbo.updateIpFinishedById(nodeTaskId, ipOkCount)
                    print '任务%s扫描完成进度：' % (nodeTaskId) + str(ipOkCount) + '/' + str(iptotal) + '\r',
                    sys.stdout.flush()
                    stepcounter = 0
                    # 查看任务的指令是否变化
                    newInstruction = dbo.getInstructionById(nodeTaskId)
                    # 如果指令不是执行
                    if newInstruction != instructionOptions['执行']:
                        # 等1秒 再执行
                        timer = threading.Timer(
                            1, func, (dbpath, inteval, step, printed))
                        timer.start()
                        # 本次任务退出
                        return

        dbo.updateStatusById(nodeTaskId, statusOptions['完成'])
        # todo:删除lastip表中的这个id记录，因为已经完成了
        logging.info("完成任务%s" % (nodeTaskId))
        # 完成一个后，直接执行下一个
        timer = threading.Timer(
            0, func, (dbpath, inteval, step, printed))
        timer.start()


class scanNode(object):

    def loadConfig(self):
        self.SERVER = 'http://127.0.0.1:8000'
        self.URL_REGISTER = '/node/register'
        self.URL_PULSE = '/node/pulse'
        self.URL_SYNCTASKINFO = '/node/syncTaskInfo'
        self.URL_NODETASKCONFIRM = '/node/nodeTaskConfirm'
        self.PASSWORD = '123'
        self.DBPATH = 'test.db'
        self.PLUGINDIR = 'plugin/'
        self.PULSE_INTEVAL = 10
        self.DOTASK_INTEVAL = 10
        self.SYNC_INTEVAL = 10
        self.pulse_delay_after_start = 0
        self.dotask_delay_after_start = 2
        self.sync_delay_after_start = 4
        self.STEP_RECORDPROGRESS = 1
        # 获得id
        self.NODEID = self.getid()
        self.lasPulseResponse = ''
        self.lasSyncResponse = ''

    def register(self):
        url = self.SERVER + self.URL_REGISTER
        p = {'pw': self.PASSWORD}
        r = '服务器连接失败，无法注册。'
        try:
            r = requests.get(url, params=p).text
        except:
            logging.info(r)
            return None
        if r.startswith("error"):
            logging.info(r)
            return None
        logging.info('注册节点成功，获得id号：%s' % (r))
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
            if nodeId == None:
                return None

            f = open('id.txt', 'w')
            f.writelines(nodeId)
            f.close()
            return nodeId

    def doTask(self):
        # 启动2秒后执行
        timer = threading.Timer(
            self.dotask_delay_after_start, func, (self.DBPATH, self.DOTASK_INTEVAL, self.STEP_RECORDPROGRESS, False))
        timer.start()

    def pulse(self):

        if self.NODEID == None:
            return

        def func():
            # sqlite要求每个线程都必须新建一个对象
            # SQLite objects created in a thread can only be used in that same thread.
            dbo = dboperator(self.DBPATH)
            url = self.SERVER + self.URL_PULSE
            ipLeft = dbo.getIpLeftAll()
            p = {'nodeID': self.NODEID, 'ipLeft': ipLeft}
            r = 'pulse线程：无法连接服务器。'
            try:
                r = requests.get(url, params=p).text
                if r.startswith("error"):
                    logging.info(r)
                    self.lasPulseResponse = r
                    return
            except:
                # 判断是否与最后一条相等，不让一直刷屏
                if self.lasPulseResponse != r:
                    logging.info(r)
                    self.lasPulseResponse = r

            if r != 'pulse线程：无法连接服务器。':
                if r == 'no task now!':
                    # 判断是否与最后一条相等，不让一直刷屏
                    if self.lasPulseResponse != r:
                        logging.info(r)
                        self.lasPulseResponse = r

                else:
                    self.lasPulseResponse = r
                    nodeTasks = eval(r)
                    logging.info("接收到%d条任务。" % (len(nodeTasks)))

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
        # 启动后直接执行
        timer = threading.Timer(self.pulse_delay_after_start, func)
        timer.start()

    def syncTaskInfo(self):
        def func():
            # sqlite要求每个线程都必须新建一个对象
            # SQLite objects created in a thread can only be used in that same thread.
            dbo = dboperator(self.DBPATH)
            url = self.SERVER + self.URL_SYNCTASKINFO
            ipFinishedList = dbo.getIpFinishedFromUnfinishedTasks()
            jsonstr = json.dumps(ipFinishedList)
            p = {'nodeID': self.NODEID, 'nodeTaskProcess': jsonstr}
            r = '同步任务线程：无法连接服务器。'
            try:
                r = requests.get(url, params=p).text
                if r.startswith("error"):
                    logging.info(r)
                    self.lasSyncResponse = r
                    return
            except:
                # 判断是否与最后一条相等，不让一直刷屏
                if self.lasSyncResponse != r:
                    logging.info(r)
                    self.lasSyncResponse = r
            if r != '同步任务线程：无法连接服务器。':
                if r == 'no task instruction changed!':
                    # 判断是否与最后一条相等，不让一直刷屏
                    if self.lasSyncResponse != r:
                        logging.info(r)
                        self.lasSyncResponse = r

                else:
                    self.lasSyncResponse = r
                    instructionChangedTasks = eval(r)
                    logging.info("接收到%d条任务更新指示。" %
                                 (len(instructionChangedTasks)))

                    for task in instructionChangedTasks:
                        ntid = task['nodeTaskID']
                        instruction = task['instruction']
                        dbo.updateInstructionById(ntid, instruction)  # 更新任务指示
            timer = threading.Timer(self.SYNC_INTEVAL, func)
            timer.start()
        # 启动4后执行
        timer = threading.Timer(self.sync_delay_after_start, func)
        timer.start()


if __name__ == '__main__':
    node = scanNode()
    node.loadConfig()
    node.pulse()
    node.doTask()
    node.syncTaskInfo()
