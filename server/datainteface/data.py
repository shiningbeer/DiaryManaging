# -*- coding:utf-8 -*-
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from bson import ObjectId
import os
import json
import datetime
import sys
from IpDispatcher import IpDispatch
from Dao.dao import daoMongo, Const, statusOptions, instructionOptions

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

ipFilePath = os.path.split(os.path.realpath(__file__))[0] + "/targets"

dao = daoMongo()
const = Const()


def getLogUser(req):
    username = req.session['username']
    return HttpResponse(username)

#-------tasks----------------


def getTasks(req):
    orderby = req.GET['orderby']
    result = []
    tks = dao.getAllTasks(orderby)
    for d in tks:
        d[const.pubTime] = d[const.pubTime].strftime('%Y-%m-%d %H:%M')
        if d[const.startTime] != None:
            d[const.startTime] = d[const.startTime].strftime('%Y-%m-%d %H:%M')
        if d[const.endTime] != None:
            d[const.endTime] = d[const.endTime].strftime('%Y-%m-%d %H:%M')
        taskid = d[const.id]
        # 如果标志已经完成，不用再计算ipfinished
        if d[const.status] == statusOptions['完成']:
            d[const.ipFinished] = d[const.ipTotal]
        # 计算所有节点的ipfinished之和
        else:
            ipfinishedlist = dao.getNodeTasks_all_by_taskID(taskid)
            ipfinished_all = 0
            complete = True
            for item in ipfinishedlist:
                ipfinished_all = ipfinished_all + item[const.ipFinished]
                if item[const.status] != statusOptions['完成']:
                    complete = False

            d[const.ipFinished] = ipfinished_all
            # 根据finished和total是否相等判断任务是否完成，另外也可以根据每个子任务是否都完成来判断。
            if d[const.ipTotal] == ipfinished_all | |complete:  # 如果相等，则更新
                d[const.status] = statusOptions['完成']
                dao.modiTask_status_by_taskID(taskid, statusOptions['完成'])
                d[const.ipFinished] = d[const.ipTotal]

        result.append(d)
    return HttpResponse(json.dumps(result))


def upNewTask(req):
    task = eval(req.GET['newtask'])
    for plugin in task['pluginFiles']:
        name = task['name'] + "_" + plugin
        ipFiles = task['ipFiles']
        user = task['user']
        description = task['description']
        dao.addNewTask(name, user, description, ipFiles, plugin)
    return HttpResponse("")


def upDeleteTask(req):
    taskid = req.GET['taskid']
    dao.delTask_by_taskID(taskid)
    # dao.modiTask_status_by_taskID(taskid, statusOptions['删除'])
    dao.modiNodeTask_instruction_by_taskID(taskid, instructionOptions['删除'])
    dao.modiNodeTask_instructionChanged_by_taskID(taskid, True)
    return HttpResponse("")


def upNewStatusForTask(req):
    params = eval(req.GET['params'])
    taskid = params['taskId']
    status = int(params['status'])
    dao.modiTask_status_by_taskID(taskid, status)
    if status == statusOptions['执行']:
        dao.modiNodeTask_instruction_by_taskID(
            taskid, instructionOptions['执行'])
    if status == statusOptions['暂停']:
        dao.modiNodeTask_instruction_by_taskID(
            taskid, instructionOptions['暂停'])
    dao.modiNodeTask_instructionChanged_by_taskID(taskid, True)

    return HttpResponse("")


def upStartTask(req):
    param = eval(req.GET['param'])
    taskId = param['taskId']
    list_nodes = param['participatingNodes']
    # 获取任务的ipfile
    task = dao.findTask_by_taskID(taskId)
    ipFiles = task[const.ipFiles]
    plugin = task[const.plugin]
    task_name = task[const.taskName]

    # 读取ipfile
    lines = []
    for ipFile in ipFiles:
        f = open(os.path.join(ipFilePath, ipFile), 'r')
        for line in f.readlines():
            lines.append(line)
        f.close()

    # 按node个数均分ip,顺手获取这个任务的ip总数
    length = len(list_nodes)
    totalsum, dispatchedList = IpDispatch(lines, length)

    # 把均分好的ip分配给node,组织好nodetask的信息并保存
    for i in range(0, length):
        task_id = taskId
        node_id = list_nodes[i]
        ip_range = []
        sum = 0
        # dispatchedList里面的元素是个字典，计算一下分配给这个node的ip数
        for item in dispatchedList[i]:
            print item
            sum = sum + item['count']
            ip_range.append(item['range'])
        ip_total = sum

        dao.addNodeTask(task_id, task_name, node_id,
                        ip_range, plugin, ip_total)

    # 将总数保存到这个任务
    dao.modiTask_ipTotal_by_taskID(taskId, totalsum)
    # 改变status为执行
    dao.modiTask_status_by_taskID(taskId, statusOptions['执行'])
    # 记录开始时间
    dao.modiTask_startTime_by_taskID(taskId, datetime.datetime.now())
    return HttpResponse("")


#-------ipfile----------------

def upDeleteIpFile(req):
    filename = req.GET['fileName']
    os.remove(os.path.join(os.path.split(
        os.path.realpath(__file__))[0] + "/targets", filename))
    return HttpResponse("")


def uploadFileIP(request):
    if request.method == "POST":    # 请求方法为POST时，进行处理
        myFile = request.FILES.get("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            return HttpResponse("no files for upload!")
        destination = open(os.path.join(os.path.split(os.path.realpath(__file__))[
            0] + "/targets", myFile.name), 'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():      # 分块写入文件
            destination.write(chunk)
        destination.close()
        return HttpResponse("upload over")


def getIpFiles(request):
    x = os.listdir(os.path.join(os.path.split(
        os.path.realpath(__file__))[0] + "/targets"))
    return HttpResponse(json.dumps(x))


#-------plugin----------------

def upDeletePluginFile(req):
    filename = req.GET['fileName']
    os.remove(os.path.join(os.path.split(
        os.path.realpath(__file__))[0] + "/myplugins", filename))
    return HttpResponse("")


def uploadFilePlugin(request):
    if request.method == "POST":    # 请求方法为POST时，进行处理
        myFile = request.FILES.get("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            return HttpResponse("no files for upload!")
        destination = open(os.path.join(os.path.split(os.path.realpath(__file__))[
            0] + "/myplugins", myFile.name), 'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():      # 分块写入文件
            destination.write(chunk)
        destination.close()
        return HttpResponse("upload over")


def getPluginFiles(request):
    x = os.listdir(os.path.join(os.path.split(
        os.path.realpath(__file__))[0] + "//myplugins"))
    return HttpResponse(json.dumps(x))


#--------------nodes----------------
def getActiveNodes(request):
    result = dao.getAllNodes()
    nodes = []
    for d in result:
        n = {}
        n['id'] = d[const.id]
        n['ipLeft'] = d[const.ipLeft]
        nodes.append(n)
    return HttpResponse(json.dumps(nodes))
