# -*- coding:utf-8 -*-
from abc import ABCMeta, abstractmethod
from pymongo import MongoClient as mc
from bson import ObjectId
import pymongo
import datetime
import sys

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

statusOptions = {"删除": -1, "未开始": 0, "执行": 1, "暂停": 2, "完成": 3}
instructionOptions = {"删除": -1, "执行": 0, "暂停": 1}


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


class daoMongo(object):
    # 构造时连接数据库
    def __init__(self):
        self.client = mc()
        self.db = self.client.scantool

#--------scanningTasks表操作--------------
    def getAllTasks(self, orderby_field):
        coll = self.db.scanningTasks
        cur = coll.find().sort(orderby_field, pymongo.DESCENDING)
        tks = []
        for d in cur:
            d[const.id] = d[const.o_id].__str__()
            d.pop(const.o_id)
            tks.append(d)
        return tks

    def addNewTask(self, name, user, description, ipfiles, plugin):
        coll = self.db.scanningTasks
        newtask = {}
        newtask[const.name] = name
        newtask[const.user] = user
        newtask[const.description] = description
        newtask[const.ipFiles] = ipfiles
        newtask[const.plugin] = plugin
        newtask[const.pubTime] = datetime.datetime.today()
        newtask[const.startTime] = None
        newtask[const.endTime] = None
        newtask[const.ipTotal] = None
        newtask[const.ipFinished] = 0
        newtask[const.status] = statusOptions['未开始']
        return coll.insert_one(newtask)

    def findTask_by_taskID(self, task_id):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.find_one({const.o_id: oid})

    def delTask_by_taskID(self, task_id):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.remove({const.o_id: oid})

    def modiTask_ipTotal_by_taskID(self, task_id, ipTotal):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.update({const.o_id: oid}, {"$set": {const.ipTotal: ipTotal}})

    def modiTask_status_by_taskID(self, task_id, status):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.update({const.o_id: oid}, {"$set": {const.status: status}})

    def modiTask_ipFinished_by_taskID(self, task_id, ipFinished):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.update({const.o_id: oid}, {"$set": {const.ipFinished: ipFinished}})

    def modiTask_startTime_by_taskID(self, task_id, startTime):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.update({const.o_id: oid}, {"$set": {const.startTime: startTime}})

    def modiTask_endTime_by_taskID(self, task_id, endTime):
        coll = self.db.scanningTasks
        oid = ObjectId(task_id)
        return coll.update({const.o_id: oid}, {"$set": {const.endTime: endTime}})


#--------nodes表操作--------------

    def getAllNodes(self):
        coll = self.db.nodes
        cur = coll.find()
        nodes = []
        for d in cur:
            d.pop(const.o_id)
            nodes.append(d)
        return nodes

    def getOneNode_by_nodeID(self, nodeID):
        coll = self.db.nodes
        return coll.find_one({const.id: nodeID})

    def addNode(self, nodeID):
        coll = self.db.nodes
        node = {}
        node[const.id] = nodeID
        node[const.pulseTime] = datetime.datetime.now()
        node[const.ipLeft] = 0
        return coll.insert_one(node)

    def delNode_by_nodeID(self, nodeID):
        coll = self.db.nodes
        return coll.remove({const.id: nodeID})

    def modiNode_pulse_by_nodeID(self, nodeID):
        coll = self.db.nodes
        pulsetime = datetime.datetime.now()
        return coll.update({const.id: nodeID}, {"$set": {const.pulseTime: pulsetime}})

    def modiNode_ipLeft_by_nodeID(self, nodeID, ipLeft):
        coll = self.db.nodes
        return coll.update({const.id: nodeID}, {"$set": {const.ipLeft: ipLeft}})

    def modiNode_status_by_nodeID(self, nodeID, nodeStatus):
        coll = self.db.nodes
        return coll.update({const.id: nodeID}, {"$set": {const.status: nodeStatus}})


#--------nodeTasks表操作--------------
    def getNodeTasks_all_by_nodeID(self, nodeid):
        coll = self.db.nodeTasks
        cur = coll.find({const.nodeId: nodeid})
        nodeTasks = []
        for d in cur:
            d[const.id] = d[const.o_id].__str__()
            d.pop(const.o_id)
            nodeTasks.append(d)
        return nodeTasks

    def getNodeTasks_unfetched_by_nodeID(self, nodeID):
        coll = self.db.nodeTasks
        cur = coll.find(
            {const.nodeId: nodeID, const.status: statusOptions['未开始'], const.instruction: instructionOptions['执行']})
        nodeTasks = []
        for d in cur:
            d[const.id] = d[const.o_id].__str__()
            d.pop(const.o_id)
            nodeTasks.append(d)
        return nodeTasks

    def getNodeTasks_instructionChanged_by_nodeID(self, nodeID):
        coll = self.db.nodeTasks
        cur = coll.find(
            {const.nodeId: nodeID, const.instructionChanged: True})
        nodeTasks = []
        for d in cur:
            d[const.id] = d[const.o_id].__str__()
            d.pop(const.o_id)
            nodeTasks.append(d)
        return nodeTasks

    def addNodeTask(self, taskId, nodeId, ipRange, plugin, ipTotal):
        coll = self.db.nodeTasks
        nodeTask = {}
        nodeTask[const.taskId] = taskId
        nodeTask[const.nodeId] = nodeId
        nodeTask[const.ipRange] = ipRange
        nodeTask[const.plugin] = plugin
        nodeTask[const.ipTotal] = ipTotal
        nodeTask[const.startTime] = datetime.datetime.now()
        nodeTask[const.endTime] = None
        nodeTask[const.ipFinished] = 0
        nodeTask[const.status] = statusOptions['未开始']
        nodeTask[const.instruction] = instructionOptions['执行']
        nodeTask[const.instructionChanged] = False
        return coll.insert_one(nodeTask)

    def modiNodeTask_status_by_nodeTaskID(self, nodeTaskID, status):
        coll = self.db.nodeTasks
        oid = ObjectId(nodeTaskID)
        return coll.update({const.o_id: oid}, {"$set": {const.status: status}})

    def modiNodeTask_ipFinished_by_nodeTaskID(self, nodeTaskID, ipFinished):
        coll = self.db.nodeTasks
        oid = ObjectId(nodeTaskID)
        return coll.update({const.o_id: oid}, {"$set": {const.ipFinished: ipFinished}})

    def modiNodeTask_endTime_by_nodeTaskID(self, nodeTaskID, endtime):
        coll = self.db.nodeTasks
        oid = ObjectId(nodeTaskID)
        return coll.update({const.o_id: oid}, {"$set": {const.endTime: endtime}})

    def modiNodeTask_instruction_by_taskID(self, taskID, instruction):
        coll = self.db.nodeTasks
        return coll.update({const.taskId: taskID}, {"$set": {const.instruction: instruction}})

    def modiNodeTask_instructionChanged_by_taskID(self, taskID, instructionChanged):
        coll = self.db.nodeTasks
        oid = ObjectId(nodeTaskID)
        return coll.update({const.taskId: taskID}, {"$set": {const.instructionChanged: instructionChanged}})
