# -*- coding:utf-8 -*-

import os
import requests
import json
import datetime
import sys
import threading
from dbOperator import dboperator, statusOptions, instructionOptions
from serverCon import serverCon
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
        self.taskName = 'taskName'


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


def scanFunc(pluginscanfunc, ip):
    pluginscanfunc(ip)


def taskfunc(scannode, printed):
    '''
    ### task线程函数，定时从数据库读取未完成任务，设置好参数后调用插件执行任务
    - 参数说明
     - scannode:调用本线程函数的scanNode类实例
     - printed:上次打印的信息
    - 这个线程函数一放在类里面就报错，exec语句无法执行，所以放外面了，拿scannode做参数传过来
    '''
    tag = 'task线程->'
    dbo = dboperator(scannode.DBPATH)
    # 先删除标记成删除的任务

    task = dbo.getOneTaskForExecute()
    r = '目前无可执行任务。'
    # 如果无任务，打印信息，定时下一次执行
    if task == None:
        if printed != r:
            logging.info(tag + r)
            printed = r
        timer = threading.Timer(
            scannode.DOTASK_INTEVAL, taskfunc, (scannode, printed))
        timer.start()
        return
    # 如果有任务
    nodeTaskId, taskName, plugin, ipranges_str, iptotal = task  # 获取task各字段（task是个元组）
    # 把后缀名.py去掉
    plugin = plugin[0:len(plugin) - 3]

    r = '未找到插件:'
    try:
        exec("from plugin import " + plugin + " as scanning_plugin")
    # 如果未找到插件(执行exec出错)，则打印信息，定时下一次执行
    except:
        if printed != r:
            logging.info(tag + r + plugin)
            printed = r
        timer = threading.Timer(
            scannode.DOTASK_INTEVAL, taskfunc, (scannode, printed))
        timer.start()
        return
    r = "开始任务%s" % (nodeTaskId)
    logging.info(tag + r)
    printed = r
    ipranges = eval(ipranges_str)  # 获取ip集
    lastip = dbo.getLastIpById(nodeTaskId)  # 加载执行进度

    # 计算需要扫描的ip集,已经扫描的个数
    ipRangesForScan, ipOkCount = caculateScaningIpRange(
        ipranges, lastip)
    stepcounter = 0  # 每满step个存储一次进度
    f = open('result/' + taskName + '_' + nodeTaskId + '.txt', 'a')
    for iprange in ipRangesForScan:
        start, end = iprange
        for i in range(start, end + 1):
            # 计数，到step个时，存储扫描到哪里,扫描了几个
            stepcounter = stepcounter + 1
            ipOkCount = ipOkCount + 1
            result = scanning_plugin.scan(str(IP(i)))
            f.writelines(json.dumps(result) + '\n')
            f.flush()
            if stepcounter == scannode.STEP_RECORDPROGRESS:
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
                        1, taskfunc, (scannode, printed))
                    timer.start()
                    # 本次任务退出
                    f.close()
                    return
    f.close()
    dbo.updateStatusById(nodeTaskId, statusOptions['完成'])
    # todo:删除lastip表中的这个id记录，因为已经完成了
    logging.info(tag + "完成任务%s" % (nodeTaskId))
    # 完成一个后，直接执行下一个
    timer = threading.Timer(
        0, taskfunc, (scannode, printed))
    timer.start()


class scanNode(object):

    def __init__(self):
        self.serverCon = serverCon()
        self.DBPATH = 'test.db'
        self.PLUGINDIR = 'plugin/'
        self.PULSE_INTEVAL = 10
        self.DOTASK_INTEVAL = 10
        self.SYNC_INTEVAL = 10
        self.REPORTTASKCOMPLETE_INTEVAL = 10
        self.pulse_delay_after_start = 0
        self.dotask_delay_after_start = 2
        self.sync_delay_after_start = 4
        self.report_delay_after_start = 6
        self.STEP_RECORDPROGRESS = 1
        # 获得id
        self.nodeId = self.getid()
        if self.nodeId == None:
            logging.info(u'获取id失败，程序退出')
            sys.exit()
        self.serverCon.setId(self.nodeId)

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
            nodeId = self.serverCon.register()
            if nodeId == None:
                return None

            f = open('id.txt', 'w')
            f.writelines(nodeId)
            f.close()
            return nodeId

    def isPluginExist(self, plugin):
        path = self.PLUGINDIR + plugin
        if os.path.exists(path):
            return True
        else:
            return False

    def pulse(self):
        '''
        执行节点心跳流程
        '''
        def pulseFunc():
            '''
            pulse线程函数，定时向Server发送心跳信息，得到返回的任务信息
            '''
            # sqlite要求每个线程都必须新建一个对象
            # SQLite objects created in a thread can only be used in that same thread.
            dbo = dboperator(self.DBPATH)
            ipLeft = dbo.getIpLeftAll()
            nodeTasks = self.serverCon.pulse(ipLeft)
            # 未获得任务，则定时再次执行
            if nodeTasks == None:
                timer = threading.Timer(self.PULSE_INTEVAL, pulseFunc)
                timer.start()
                return
            # 获得任务，保存后定时再执行
            for task in nodeTasks:
                ntid = task[const.id]
                plugin = task[const.plugin]
                # 如果这个任务的插件不存在，则提示等待下载或拷入，循环至下一个
                if self.isPluginExist(plugin) != True:
                    logging.info("任务%s所指定的插件%s不存在，请等待下载线程下载，或请直接将相应插件拷入plugin文件夹。" % (
                        ntid, plugin))
                    continue
                # 如果任务已经存在，提示不保存，向服务器确认该任务，循环至下一个
                if dbo.isExistById(ntid):
                    logging.info("任务%s已存在，不予保存。" % (ntid))
                    continue
                # 保存任务，并向服务器确认
                ipRange = json.dumps(task[const.ipRange])
                ipTotal = task[const.ipTotal]
                taskName = task[const.taskName]
                dbo.insertTask(ntid, taskName, ipRange, plugin, ipTotal)
            logging.info("已保存任务，向服务器发送确认信息。")
            self.serverCon.nodeTaskConfirm()
            # 定时下次执行
            timer = threading.Timer(self.PULSE_INTEVAL, pulseFunc)
            timer.start()

        # 执行pulse
        timer = threading.Timer(self.pulse_delay_after_start, pulseFunc)
        timer.start()

    def syncTaskInfo(self):
        '''
        执行节点同步任务流程
        '''
        def syncfunc():
            '''
            sync线程函数，定时向服务器发送任务进度，得到返回的有任务指令修改的任务
            '''
            dbo = dboperator(self.DBPATH)
            ipFinishedList = dbo.getIpFinishedFromNotFinisedAndNotifiedTasks()
            instructionChangedTasks = self.serverCon.syncTaskInfo(
                ipFinishedList)
            # 未获得任务，则定时再次执行
            if instructionChangedTasks == None:
                timer = threading.Timer(self.SYNC_INTEVAL, syncfunc)
                timer.start()
                return
            # 获得任务，保存后定时再执行
            for task in instructionChangedTasks:
                ntid = task['nodeTaskID']
                instruction = task['instruction']
                dbo.updateInstructionById(ntid, instruction)  # 更新任务指示
            # 向服务器确认收到
            self.serverCon.instructionChangedConfirm()
            timer = threading.Timer(self.SYNC_INTEVAL, syncfunc)
            timer.start()
        # 执行
        timer = threading.Timer(self.sync_delay_after_start, syncfunc)
        timer.start()

    def reportTaskComplete(self):
        '''
        执行节点报告任务完成流程
        '''
        def reportfunc():
            '''
            report线程函数，定时将已经完成的任务报告给服务器，收到服务器确认消息后保存
            '''
            dbo = dboperator(self.DBPATH)
            completeTasks = dbo.getFinished_but_not_report_Tasks()
            success = self.serverCon.reportTaskComplete(completeTasks)
            # 报告不成功，则定时再次执行
            if success == False:
                timer = threading.Timer(
                    self.REPORTTASKCOMPLETE_INTEVAL, reportfunc)
                timer.start()
                return
            # 报告成功，则将本地完成的任务的Status从完成改为完成且已通知
            for nodetaskid in completeTasks:
                dbo.updateStatusById(
                    nodetaskid, statusOptions['完成并已通知'])
            timer = threading.Timer(
                self.REPORTTASKCOMPLETE_INTEVAL, reportfunc)
            timer.start()
        # 执行
        timer = threading.Timer(
            self.report_delay_after_start, reportfunc)
        timer.start()

    def doTask(self):
        '''
        执行节点执行任务流程
        '''
        # 执行
        timer = threading.Timer(
            self.dotask_delay_after_start, taskfunc, (self, False))
        timer.start()


if __name__ == '__main__':
    node = scanNode()
    node.pulse()
    node.doTask()
    node.syncTaskInfo()
    node.reportTaskComplete()
