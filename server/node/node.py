# -*- coding:utf-8 -*-
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
import os
import json
from datetime import datetime
import sys
import time
import hashlib
from Dao.dao import daoMongo, Const, statusOptions, instructionOptions

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

dao = daoMongo()
const = Const()


def register(req):
    try:
        pw = req.GET['pw']
    except:
        return HttpResponse("error: param error")

    if pw != "123":
        return HttpResponse("error: password wrong")
    else:
        m = hashlib.md5(str(time.clock()).encode('utf-8'))
        nodeID = m.hexdigest()
        dao.addNode(nodeID)
        return HttpResponse(nodeID)


def pulse(req):
    try:
        ipLeft = int(req.GET['ipLeft'])
        nodeID = req.GET['nodeID']
    except:
        return HttpResponse("error:param error")
    # dao.modiNodeTask_status_by_nodeTaskID(
    #     '5a1429db5919ba5b98435f08', statusOptions['未开始'])
    if dao.getOneNode_by_nodeID(nodeID) != None:
        dao.modiNode_pulse_by_nodeID(nodeID)
        unfetchedTasks = dao.getNodeTasks_unfetched_by_nodeID(nodeID)
        if len(unfetchedTasks) == 0:
            return HttpResponse("no task now!")
        for task in unfetchedTasks:
            # task[const.startTime] = task[const.startTime].strftime(
            #     '%Y-%m-%d %H:%M')
            # 除去不需要的
            task.pop(const.startTime)
            task.pop(const.endTime)  # null无法被eval识别
            task.pop(const.instructionChanged)  # false无法被eval识别
            task.pop(const.nodeId)
            task.pop(const.ipFinished)
            task.pop(const.taskId)
            task.pop(const.status)
            task.pop(const.instruction)
        result = json.dumps(unfetchedTasks)
        return HttpResponse(result)
    else:
        return HttpResponse("error: nodeid not registered!")


def taskProcessReport(req):
    return HttpResponse("")


def nodeTaskConfirm(req):
    try:
        nodeTaskid = req.GET['id']
    except:
        return HttpResponse("error:param error when confirm task")
    dao.modiNodeTask_status_by_nodeTaskID(nodeTaskid, statusOptions['执行'])
    return HttpResponse("task:" + nodeTaskid + " has been confirmed!")
